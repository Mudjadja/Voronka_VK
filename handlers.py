# handlers.py
import logging
from datetime import datetime
from user_state import State
from keyboards import Keyboards
from messages import Messages

logger = logging.getLogger(__name__)


class Handlers:
    """Обработчики сообщений"""

    def __init__(self, bot, db, photo_handler):
        self.bot = bot
        self.db = db
        self.photo = photo_handler
        self.keyboards = Keyboards()
        self.messages = Messages()

    def handle_start(self, user_id, state):
        """Начало работы"""
        # Ищем пользователя
        user = self.db.get_user(user_id)

        if user:
            state.data = user
            state.set_state(State.MAIN_MENU)
            self.bot.send_message(
                user_id,
                self.messages.welcome_back(user['name'], user['macro_region']),
                self.keyboards.get_start_keyboard()
            )
        else:
            state.set_state(State.WAITING_FIO)
            # Получаем username из VK
            users = self.bot.vk.users.get(user_ids=user_id, fields='screen_name')
            if users:
                state.data['username'] = users[0].get('screen_name', '')
            state.data['user_id'] = str(user_id)
            self.bot.send_message(user_id, self.messages.ask_fio())

    def handle_fio(self, user_id, message, state):
        """Обработка ФИО"""
        if not message or not message.strip():
            self.bot.send_message(user_id, self.messages.ask_fio())
            return

        state.data['name'] = message.strip()
        state.data['date_reg'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state.set_state(State.WAITING_MACRO_REGION)
        self.bot.send_message(
            user_id,
            self.messages.ask_macro_region(),
            self.keyboards.get_macro_regions_keyboard()
        )

    def handle_macro_region(self, user_id, message, state):
        """Обработка выбора макрорегиона"""
        from config import MACRO_REGIONS

        if message not in MACRO_REGIONS.values():
            self.bot.send_message(
                user_id,
                self.messages.ask_macro_region(),
                self.keyboards.get_macro_regions_keyboard()
            )
            return

        state.data['macro_region'] = message
        state.set_state(State.WAITING_SUBREGION)
        self.bot.send_message(
            user_id,
            self.messages.ask_subregion(message),
            self.keyboards.get_subregions_keyboard(message)
        )

    def handle_subregion(self, user_id, message, state):
        """Обработка выбора подрегиона"""
        from config import SUBREGIONS

        macro = state.data['macro_region']
        if message not in SUBREGIONS.get(macro, []):
            self.bot.send_message(
                user_id,
                self.messages.ask_subregion(macro),
                self.keyboards.get_subregions_keyboard(macro)
            )
            return

        # Сохраняем регистрацию
        if self.db.save_registration(state.data, macro, message):
            state.data['subregion'] = message
            state.set_state(State.MAIN_MENU)
            self.bot.send_message(
                user_id,
                self.messages.registration_complete(state.data['name']),
                self.keyboards.get_start_keyboard()
            )
        else:
            self.bot.send_message(user_id, "❌ Ошибка сохранения")
            state.set_state(State.START)

    def handle_main_menu(self, user_id, message, state):
        """Главное меню"""
        if message == 'Ввести данные по встрече':
            state.clear_temp()
            state.set_state(State.WAITING_CLIENT)
            self.bot.send_message(
                user_id,
                self.messages.ask_client(),
                self.keyboards.get_back_keyboard()
            )
        else:
            self.bot.send_message(
                user_id,
                self.messages.main_menu(),
                self.keyboards.get_start_keyboard()
            )

    def handle_question(self, user_id, message, state, event):
        """Обработка вопросов анкеты"""
        current = state.state

        # Специальная обработка для фото
        if current == State.WAITING_PHOTO:
            self.handle_photo(user_id, state, event)
            return

        # Обработка выбора услуг
        if current == State.WAITING_SERVICES_SELECTION:
            self.handle_services_selection(user_id, message, state)
            return

        if current == State.WAITING_SERVICES_ADD_MORE:
            self.handle_services_selection(user_id, message, state)
            return

        # Специальная обработка для выбора после предыдущей встречи
        if current == State.WAITING_PREVIOUS_CHOICE:
            self.handle_previous_choice(user_id, message, state)
            return

        # Проверка текста
        if not message or not message.strip():
            self.bot.send_message(user_id, "Пожалуйста, введите ответ:", self.keyboards.get_back_keyboard())
            return

        # Обработка вопросов
        if current == State.WAITING_CLIENT:
            state.temp['client'] = message.strip()
            state.set_state(State.WAITING_INN)
            self.bot.send_message(user_id, self.messages.ask_inn(), self.keyboards.get_back_keyboard())

        elif current == State.WAITING_INN:
            state.temp['inn'] = message.strip()
            state.set_state(State.WAITING_SECOND_MEETING)
            self.bot.send_message(user_id, self.messages.ask_second_meeting(), self.keyboards.get_yes_no_keyboard())

        elif current == State.WAITING_SECOND_MEETING:
            state.temp['second_meeting'] = message

            if message.lower() == 'да':
                # Ищем предыдущую встречу
                prev = self.db.find_previous_meeting(state.temp['inn'], state.data['macro_region'])
                if prev:
                    # Сохраняем данные предыдущей встречи
                    state.previous_data = prev
                    # Показываем информацию о предыдущей встрече
                    info = self.messages.format_previous_meeting(prev)
                    self.bot.send_message(user_id, info)
                    # Спрашиваем, что делать
                    state.set_state(State.WAITING_PREVIOUS_CHOICE)
                    self.bot.send_message(
                        user_id,
                        "Что вы хотите сделать?\n\n"
                        "📌 Продолжить ввод - заполнить новые данные\n"
                        "📌 Использовать предыдущие - скопировать данные из прошлой встречи и завершить опросник",
                        self.keyboards.get_previous_choice_keyboard()
                    )
                else:
                    # Нет предыдущих встреч, продолжаем
                    self.bot.send_message(user_id,
                                          "❌ Предыдущих встреч по этому ИНН не найдено. Продолжаем ввод новых данных.")
                    state.set_state(State.WAITING_CONTACT_NAME)
                    self.bot.send_message(user_id, self.messages.ask_contact_name(), self.keyboards.get_back_keyboard())
            else:
                # Встреча не повторная, продолжаем опрос
                state.set_state(State.WAITING_CONTACT_NAME)
                self.bot.send_message(user_id, self.messages.ask_contact_name(), self.keyboards.get_back_keyboard())

        elif current == State.WAITING_CONTACT_NAME:
            state.temp['contact_name'] = message.strip()
            state.set_state(State.WAITING_CONTACT_PHONE)
            self.bot.send_message(user_id, self.messages.ask_contact_phone(), self.keyboards.get_back_keyboard())

        elif current == State.WAITING_CONTACT_PHONE:
            state.temp['contact_phone'] = message.strip()
            state.set_state(State.WAITING_COMPETITORS_USE)
            self.bot.send_message(user_id, self.messages.ask_competitors_use(), self.keyboards.get_yes_no_keyboard())

        elif current == State.WAITING_COMPETITORS_USE:
            state.temp['competitors_use'] = message
            if message.lower() == 'да':
                state.set_state(State.WAITING_COMPETITORS_SERVICES)
                self.bot.send_message(user_id, self.messages.ask_competitors_services(),
                                      self.keyboards.get_back_keyboard())
            else:
                state.set_state(State.WAITING_CONSENT_CONNECT)
                self.bot.send_message(user_id, self.messages.ask_consent_connect(),
                                      self.keyboards.get_yes_no_keyboard())

        elif current == State.WAITING_COMPETITORS_SERVICES:
            state.temp['competitors_services'] = message.strip()
            state.set_state(State.WAITING_CONSENT_CONNECT)
            self.bot.send_message(user_id, self.messages.ask_consent_connect(), self.keyboards.get_yes_no_keyboard())



        elif current == State.WAITING_CONSENT_CONNECT:
            state.temp['consent_connect'] = message
            if message.lower() == 'да':
                # Переходим к выбору услуг
                self.handle_services_connect_start(user_id, state)
            else:
                state.set_state(State.WAITING_CLIENT_FEEDBACK)
                self.bot.send_message(user_id, self.messages.ask_client_feedback(),
                                      self.keyboards.get_yes_no_keyboard())


        elif current == State.WAITING_SERVICES_CONNECT:
            from config import SERVICES_SELECTION_REGIONS
            macro_region = state.data.get('macro_region', '')
            if macro_region in SERVICES_SELECTION_REGIONS:
                # Для регионов Центр и Урал - уже должны быть в другом состоянии
                # Если мы здесь, значит пользователь не выбрал услуги, а ввел текст
                if message and message.strip():
                    state.temp['services_connect'] = message.strip()
                    state.set_state(State.WAITING_CLIENT_FEEDBACK)
                    self.bot.send_message(user_id, self.messages.ask_client_feedback(),
                                          self.keyboards.get_yes_no_keyboard())
                else:
                    self.bot.send_message(user_id, "Пожалуйста, выберите услуги:",
                                          self.keyboards.get_services_keyboard())
            else:
                # Для других регионов - обычный ввод текста
                if message and message.strip():
                    state.temp['services_connect'] = message.strip()
                    state.set_state(State.WAITING_CLIENT_FEEDBACK)
                    self.bot.send_message(user_id, self.messages.ask_client_feedback(),
                                          self.keyboards.get_yes_no_keyboard())
                else:
                    self.bot.send_message(user_id, "Пожалуйста, введите услуги:",
                                          self.keyboards.get_back_keyboard())


        elif current == State.WAITING_CLIENT_FEEDBACK:
            state.temp['client_feedback'] = message
            if message.lower() == 'да':
                state.set_state(State.WAITING_FEEDBACK_CONTACT)
                self.bot.send_message(user_id, self.messages.ask_feedback_contact(), self.keyboards.get_back_keyboard())
            else:
                state.set_state(State.WAITING_AGREEMENT)
                self.bot.send_message(user_id, self.messages.ask_agreement(), self.keyboards.get_yes_no_keyboard())

        elif current == State.WAITING_FEEDBACK_CONTACT:
            state.temp['feedback_contact'] = message.strip()
            state.set_state(State.WAITING_AGREEMENT)
            self.bot.send_message(user_id, self.messages.ask_agreement(), self.keyboards.get_yes_no_keyboard())

        elif current == State.WAITING_AGREEMENT:
            state.temp['agreement'] = message
            state.set_state(State.WAITING_SUMMARY)
            self.bot.send_message(user_id, self.messages.ask_summary(), self.keyboards.get_back_keyboard())

        elif current == State.WAITING_SUMMARY:
            state.temp['summary'] = message.strip()
            state.set_state(State.WAITING_PHOTO)
            self.bot.send_message(user_id, self.messages.ask_photo(), self.keyboards.get_back_keyboard())

        elif current == State.WAITING_SERVICES_CONNECT:
            from config import SERVICES_SELECTION_REGIONS

            macro_region = state.data.get('macro_region', '')

            if macro_region in SERVICES_SELECTION_REGIONS:
                # Для регионов Центр и Урал - показываем выбор услуг
                state.set_state(State.WAITING_SERVICES_SELECTION)
                self.bot.send_message(user_id, self.messages.ask_services_selection(),
                                      self.keyboards.get_services_keyboard())
            else:
                # Для других регионов - обычный ввод текста
                if message and message.strip():
                    state.temp['services_connect'] = message.strip()
                    state.set_state(State.WAITING_CLIENT_FEEDBACK)
                    self.bot.send_message(user_id, self.messages.ask_client_feedback(),
                                          self.keyboards.get_yes_no_keyboard())
                else:
                    self.bot.send_message(user_id, "Пожалуйста, введите услуги:",
                                          self.keyboards.get_back_keyboard())

    def handle_previous_choice(self, user_id, message, state):
        """Обработка выбора после показа предыдущей встречи"""
        if message == 'Продолжить ввод':
            # Продолжаем заполнение новых данных
            state.set_state(State.WAITING_CONTACT_NAME)
            self.bot.send_message(user_id, self.messages.ask_contact_name(), self.keyboards.get_back_keyboard())

        elif message == 'Использовать предыдущие':
            # Копируем данные из предыдущей встречи
            prev = state.previous_data
            if prev:
                # Сохраняем клиента и ИНН из текущего ввода
                client = state.temp.get('client', '')
                inn = state.temp.get('inn', '')

                # Создаем новые данные для сохранения
                new_meeting = {
                    'client': client,
                    'inn': inn,
                    'contact_name': prev.get('Контакт ФИО', ''),
                    'contact_phone': prev.get('Контакт номер', ''),
                    'second_meeting': 'Да',
                    'competitors_use': prev.get('Пользуется услугами', ''),
                    'competitors_services': prev.get('Услуги конкурентов', ''),
                    'consent_connect': prev.get('Новые услуги РТК (согл)', ''),
                    'services_connect': prev.get('Информация по новым услугам РТК (подкл)', ''),
                    'client_feedback': prev.get('Рекомендации', ''),
                    'feedback_contact': prev.get('Контакты рекомендации', ''),
                    'agreement': prev.get('Договоренности', ''),
                    'summary': prev.get('Резюме встречи', ''),
                    'foto': 'скопировано из предыдущей встречи',
                    'date_today': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }

                # Сохраняем встречу
                if self.db.save_meeting(
                        state.data, new_meeting,
                        state.data['macro_region'],
                        state.data.get('subregion', '')
                ):
                    self.bot.send_message(user_id,
                                          f"✅ Данные скопированы из предыдущей встречи и сохранены!\n"
                                          f"📅 Дата встречи: {new_meeting['date_today']}\n"
                                          f"🏢 Клиент: {client}\n"
                                          f"🔢 ИНН: {inn}",
                                          self.keyboards.get_start_keyboard())
                else:
                    self.bot.send_message(user_id,
                                          "❌ Ошибка сохранения данных",
                                          self.keyboards.get_start_keyboard())

                state.set_state(State.MAIN_MENU)
                state.clear_temp()
                state.previous_data = None
            else:
                self.bot.send_message(user_id, "❌ Нет данных для копирования")
                state.set_state(State.WAITING_CONTACT_NAME)
                self.bot.send_message(user_id, self.messages.ask_contact_name(), self.keyboards.get_back_keyboard())

        elif message == '🔙 Назад':
            # Возвращаемся к вопросу о повторной встрече
            state.set_state(State.WAITING_SECOND_MEETING)
            self.bot.send_message(user_id, self.messages.ask_second_meeting(), self.keyboards.get_yes_no_keyboard())

        else:
            self.bot.send_message(
                user_id,
                "Пожалуйста, выберите действие:",
                self.keyboards.get_previous_choice_keyboard()
            )

    def handle_photo(self, user_id, state, event):
        """Обработка фото"""
        photo_url = self.photo.get_photo_url(event)

        if photo_url:
            self.bot.send_message(user_id, "📸 Сохраняю фото...")

            # Сохраняем фото и получаем только имя файла
            filename = self.photo.save_photo(
                photo_url,
                state.data['macro_region'],
                state.temp.get('client', 'unknown'),
                state.temp.get('inn', 'unknown'),
                state.data.get('name', 'unknown')
            )

            if filename:
                state.temp['foto'] = filename
                self.bot.send_message(user_id, f"✅ Фото сохранено: {filename}")
            else:
                state.temp['foto'] = 'нет фото'
                self.bot.send_message(user_id, "❌ Ошибка при сохранении фото")
        else:
            # Если фото не отправлено, проверяем текстовый ответ
            if event.text and event.text.strip():
                state.temp['foto'] = event.text.strip()
            else:
                self.bot.send_message(user_id, self.messages.ask_photo(), self.keyboards.get_back_keyboard())
                return

        # Сохраняем встречу
        state.temp['date_today'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        if self.db.save_meeting(
                state.data, state.temp,
                state.data['macro_region'],
                state.data.get('subregion', '')
        ):
            self.bot.send_message(user_id, self.messages.save_success(), self.keyboards.get_start_keyboard())
        else:
            self.bot.send_message(user_id, "❌ Ошибка сохранения", self.keyboards.get_start_keyboard())

        state.set_state(State.MAIN_MENU)
        state.clear_temp()
        state.previous_data = None

    def handle_services_selection(self, user_id, message, state):
        """Обработка выбора услуги"""
        from config import SERVICES_LIST

        logger.info(f"handle_services_selection: message={message}, state={state.state}")

        if message == '🔙 Назад':
            # Возвращаемся к вопросу о согласии на подключение
            state.set_state(State.WAITING_CONSENT_CONNECT)
            self.bot.send_message(user_id, self.messages.ask_consent_connect(),
                                  self.keyboards.get_yes_no_keyboard())
            return

        if message in ['Дальше', '➡️ Дальше', 'Дальше']:
            # Завершаем выбор услуг
            services_str = state.get_services_string()
            if services_str:
                state.temp['services_connect'] = services_str
                logger.info(f"Сохранены услуги: {services_str}")
            else:
                state.temp['services_connect'] = 'не выбрано'
                logger.info("Услуги не выбраны")

            # Переходим к следующему вопросу
            state.set_state(State.WAITING_CLIENT_FEEDBACK)
            self.bot.send_message(user_id, self.messages.ask_client_feedback(),
                                  self.keyboards.get_yes_no_keyboard())
            return

        if message in ['Добавить услугу', '➕ Добавить услугу', 'Добавить услугу']:
            # Показываем список услуг
            state.set_state(State.WAITING_SERVICES_SELECTION)
            self.bot.send_message(user_id, self.messages.ask_services_selection(),
                                  self.keyboards.get_services_keyboard())
            return

        if message in SERVICES_LIST:
            # Добавляем услугу
            state.add_service(message)
            logger.info(f"Добавлена услуга: {message}, всего: {state.get_services_string()}")
            state.set_state(State.WAITING_SERVICES_ADD_MORE)
            self.bot.send_message(user_id, self.messages.service_added(message),
                                  self.keyboards.get_services_add_more_keyboard())
            return

        # Если текущее состояние WAITING_SERVICES_SELECTION и сообщение не из списка
        if state.state == State.WAITING_SERVICES_SELECTION:
            self.bot.send_message(user_id, "Пожалуйста, выберите услугу из списка:",
                                  self.keyboards.get_services_keyboard())
        else:
            self.bot.send_message(user_id, "Пожалуйста, выберите действие:",
                                  self.keyboards.get_services_add_more_keyboard())

    def handle_services_connect_start(self, user_id, state):
        """Начало выбора услуг"""
        from config import SERVICES_SELECTION_REGIONS

        macro_region = state.data.get('macro_region', '')

        # Проверяем, нужно ли показывать выбор услуг
        if macro_region in SERVICES_SELECTION_REGIONS:
            # Для регионов Центр и Урал - показываем выбор услуг
            logger.info(f"Регион {macro_region} - показываем выбор услуг")
            state.set_state(State.WAITING_SERVICES_SELECTION)
            self.bot.send_message(user_id, self.messages.ask_services_selection(),
                                  self.keyboards.get_services_keyboard())
        else:
            # Для других регионов - обычный ввод текста
            logger.info(f"Регион {macro_region} - обычный ввод текста")
            state.set_state(State.WAITING_SERVICES_CONNECT)
            self.bot.send_message(user_id, self.messages.ask_services_connect(),
                                  self.keyboards.get_back_keyboard())
