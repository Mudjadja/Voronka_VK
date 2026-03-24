# main.py
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import logging

from config import VK_TOKEN, ensure_directories
from user_state import UserState, State
from database import Database
from photo_handler import PhotoHandler
from handlers import Handlers
from keyboards import Keyboards
from messages import Messages

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VKBot:
    def __init__(self, token):
        self.vk_session = vk_api.VkApi(token=token)
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()

        # Компоненты
        self.db = Database()
        self.photo = PhotoHandler(self.vk)
        self.handlers = Handlers(self, self.db, self.photo)
        self.keyboards = Keyboards()
        self.messages = Messages()

        # Состояния пользователей
        self.user_states = {}

        # Создание папок
        ensure_directories()

        logger.info("Бот запущен")

    def send_message(self, user_id, message, keyboard=None):
        """Отправка сообщения"""
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': 0,
                'parse_mode': 'HTML'
            }
            if keyboard:
                params['keyboard'] = keyboard.get_keyboard()

            self.vk.messages.send(**params)
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")

    def get_question_text(self, state):
        """Текст вопроса для состояния"""
        questions = {
            State.WAITING_FIO: self.messages.ask_fio,
            State.WAITING_MACRO_REGION: self.messages.ask_macro_region,
            State.WAITING_SUBREGION: lambda: self.messages.ask_subregion(''),
            State.MAIN_MENU: self.messages.main_menu,
            State.WAITING_CLIENT: self.messages.ask_client,
            State.WAITING_INN: self.messages.ask_inn,
            State.WAITING_SECOND_MEETING: self.messages.ask_second_meeting,
            State.WAITING_CONTACT_NAME: self.messages.ask_contact_name,
            State.WAITING_CONTACT_PHONE: self.messages.ask_contact_phone,
            State.WAITING_COMPETITORS_USE: self.messages.ask_competitors_use,
            State.WAITING_COMPETITORS_SERVICES: self.messages.ask_competitors_services,
            State.WAITING_CONSENT_CONNECT: self.messages.ask_consent_connect,
            State.WAITING_SERVICES_CONNECT: self.messages.ask_services_connect,
            State.WAITING_CLIENT_FEEDBACK: self.messages.ask_client_feedback,
            State.WAITING_FEEDBACK_CONTACT: self.messages.ask_feedback_contact,
            State.WAITING_AGREEMENT: self.messages.ask_agreement,
            State.WAITING_SUMMARY: self.messages.ask_summary,
            State.WAITING_PHOTO: self.messages.ask_photo
        }

        if state in questions:
            return questions[state]()
        return "Введите ответ:"

    def handle_back(self, user_id, state):
        """Обработка кнопки Назад"""
        # Если мы в состоянии выбора после предыдущей встречи, очищаем previous_data
        if state.state == State.WAITING_PREVIOUS_CHOICE:
            state.previous_data = None

        if state.go_back():
            self.resume_state(user_id, state)
            return True
        return False

    def resume_state(self, user_id, state):
        """Возобновление диалога"""
        if state.state == State.MAIN_MENU:
            self.send_message(user_id, self.messages.main_menu(), self.keyboards.get_start_keyboard())

        elif state.state == State.WAITING_MACRO_REGION:
            self.send_message(user_id, self.messages.ask_macro_region(), self.keyboards.get_macro_regions_keyboard())

        elif state.state == State.WAITING_SUBREGION:
            macro = state.data.get('macro_region', '')
            if macro:
                self.send_message(user_id, self.messages.ask_subregion(macro),
                                  self.keyboards.get_subregions_keyboard(macro))
            else:
                self.send_message(user_id, self.messages.ask_macro_region(),
                                  self.keyboards.get_macro_regions_keyboard())
        elif state.state in [State.WAITING_SERVICES_SELECTION, State.WAITING_SERVICES_ADD_MORE]:
            if state.state == State.WAITING_SERVICES_SELECTION:
                self.send_message(user_id, self.messages.ask_services_selection(),
                                  self.keyboards.get_services_keyboard())
            else:
                services_str = state.get_services_string()
                if services_str:
                    self.send_message(user_id, self.messages.service_added(services_str.split(', ')[-1]),
                                      self.keyboards.get_services_add_more_keyboard())
                else:
                    self.send_message(user_id, "Выберите услугу:",
                                      self.keyboards.get_services_keyboard())


        elif state.state == State.WAITING_PREVIOUS_CHOICE:
            self.send_message(
                user_id,
                "Что вы хотите сделать?\n\n"
                "📌 Продолжить ввод - заполнить новые данные\n"
                "📌 Использовать предыдущие - скопировать данные из прошлой встречи и завершить опросник",
                self.keyboards.get_previous_choice_keyboard()
            )

        elif state.state in [State.WAITING_SECOND_MEETING, State.WAITING_COMPETITORS_USE,
                             State.WAITING_CONSENT_CONNECT, State.WAITING_CLIENT_FEEDBACK,
                             State.WAITING_AGREEMENT]:
            question = self.get_question_text(state.state)
            self.send_message(user_id, question, self.keyboards.get_yes_no_keyboard())

        elif state.state == State.WAITING_PHOTO:
            self.send_message(user_id, self.messages.ask_photo(), self.keyboards.get_back_keyboard())

        elif state.state in [State.WAITING_CLIENT, State.WAITING_INN, State.WAITING_CONTACT_NAME,
                             State.WAITING_CONTACT_PHONE, State.WAITING_COMPETITORS_SERVICES,
                             State.WAITING_SERVICES_CONNECT, State.WAITING_FEEDBACK_CONTACT,
                             State.WAITING_SUMMARY]:
            question = self.get_question_text(state.state)
            self.send_message(user_id, question, self.keyboards.get_back_keyboard())

        elif state.state == State.WAITING_FIO:
            self.send_message(user_id, self.messages.ask_fio())

        else:
            question = self.get_question_text(state.state)
            self.send_message(user_id, question)

    def handle_message(self, event):
        """Основной обработчик сообщений"""
        user_id = event.user_id
        message = event.text or ""

        # Создаем состояние если нужно
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState(user_id)

        state = self.user_states[user_id]

        # Обработка кнопки "Назад"
        if message == '🔙 Назад':
            if self.handle_back(user_id, state):
                return
            else:
                self.send_message(user_id, "Нельзя вернуться назад", self.keyboards.get_start_keyboard())
                return

        # Маршрутизация по состояниям
        if state.state == State.START:
            self.handlers.handle_start(user_id, state)

        elif state.state == State.WAITING_FIO:
            self.handlers.handle_fio(user_id, message, state)

        elif state.state == State.WAITING_MACRO_REGION:
            self.handlers.handle_macro_region(user_id, message, state)

        elif state.state == State.WAITING_SUBREGION:
            self.handlers.handle_subregion(user_id, message, state)

        elif state.state == State.MAIN_MENU:
            self.handlers.handle_main_menu(user_id, message, state)

        elif state.state == State.WAITING_PREVIOUS_CHOICE:
            self.handlers.handle_previous_choice(user_id, message, state)


        elif state.state in [State.WAITING_CLIENT, State.WAITING_INN, State.WAITING_SECOND_MEETING,
                             State.WAITING_CONTACT_NAME, State.WAITING_CONTACT_PHONE,
                             State.WAITING_COMPETITORS_USE, State.WAITING_COMPETITORS_SERVICES,
                             State.WAITING_CONSENT_CONNECT, State.WAITING_SERVICES_CONNECT,
                             State.WAITING_SERVICES_SELECTION, State.WAITING_SERVICES_ADD_MORE,
                             State.WAITING_CLIENT_FEEDBACK, State.WAITING_FEEDBACK_CONTACT,
                             State.WAITING_AGREEMENT, State.WAITING_SUMMARY, State.WAITING_PHOTO]:
            self.handlers.handle_question(user_id, message, state, event)


        else:
            logger.warning(f"Неизвестное состояние: {state.state}")
            state.set_state(State.MAIN_MENU)
            self.send_message(user_id, "Главное меню:", self.keyboards.get_start_keyboard())

    def run(self):
        """Запуск бота"""
        logger.info("=" * 50)
        logger.info("🚀 Бот запущен")
        logger.info("=" * 50)

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    self.handle_message(event)
                except Exception as e:
                    logger.error(f"Ошибка: {e}")
                    import traceback
                    traceback.print_exc()
                    self.send_message(event.user_id, "Произошла ошибка. Попробуйте позже.")

    def get_question_text(self, state):
        """Текст вопроса для состояния"""
        questions = {
            State.WAITING_FIO: self.messages.ask_fio,
            State.WAITING_MACRO_REGION: self.messages.ask_macro_region,
            State.WAITING_SUBREGION: lambda: self.messages.ask_subregion(''),
            State.MAIN_MENU: self.messages.main_menu,
            State.WAITING_PREVIOUS_CHOICE: lambda: "Что вы хотите сделать?",
            State.WAITING_CLIENT: self.messages.ask_client,
            State.WAITING_INN: self.messages.ask_inn,
            State.WAITING_SECOND_MEETING: self.messages.ask_second_meeting,
            State.WAITING_CONTACT_NAME: self.messages.ask_contact_name,
            State.WAITING_CONTACT_PHONE: self.messages.ask_contact_phone,
            State.WAITING_COMPETITORS_USE: self.messages.ask_competitors_use,
            State.WAITING_COMPETITORS_SERVICES: self.messages.ask_competitors_services,
            State.WAITING_CONSENT_CONNECT: self.messages.ask_consent_connect,
            State.WAITING_SERVICES_SELECTION: lambda: "Выберите услугу:",
            State.WAITING_SERVICES_ADD_MORE: lambda: "Добавьте услугу или перейдите дальше:",
            State.WAITING_SERVICES_CONNECT: self.messages.ask_services_connect,
            State.WAITING_CLIENT_FEEDBACK: self.messages.ask_client_feedback,
            State.WAITING_FEEDBACK_CONTACT: self.messages.ask_feedback_contact,
            State.WAITING_AGREEMENT: self.messages.ask_agreement,
            State.WAITING_SUMMARY: self.messages.ask_summary,
            State.WAITING_PHOTO: self.messages.ask_photo
        }

        if state in questions:
            return questions[state]()
        return "Введите ответ:"


if __name__ == '__main__':
    bot = VKBot(VK_TOKEN)
    bot.run()