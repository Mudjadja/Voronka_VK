# user_state.py
import logging
from enum import Enum

# Настройка логирования
logger = logging.getLogger(__name__)


class State(Enum):
    START = 'start'
    WAITING_FIO = 'waiting_fio'
    WAITING_MACRO_REGION = 'waiting_macro_region'
    WAITING_SUBREGION = 'waiting_subregion'
    MAIN_MENU = 'main_menu'
    WAITING_CLIENT = 'waiting_client'
    WAITING_INN = 'waiting_inn'
    WAITING_SECOND_MEETING = 'waiting_second_meeting'
    WAITING_PREVIOUS_CHOICE = 'waiting_previous_choice'  # Новое состояние
    WAITING_CONTACT_NAME = 'waiting_contact_name'
    WAITING_CONTACT_PHONE = 'waiting_contact_phone'
    WAITING_COMPETITORS_USE = 'waiting_competitors_use'
    WAITING_COMPETITORS_SERVICES = 'waiting_competitors_services'
    WAITING_CONSENT_CONNECT = 'waiting_consent_connect'
    WAITING_SERVICES_CONNECT = 'waiting_services_connect'
    WAITING_CLIENT_FEEDBACK = 'waiting_client_feedback'
    WAITING_FEEDBACK_CONTACT = 'waiting_feedback_contact'
    WAITING_AGREEMENT = 'waiting_agreement'
    WAITING_SUMMARY = 'waiting_summary'
    WAITING_PHOTO = 'waiting_photo'
    WAITING_SERVICES_SELECTION = 'waiting_services_selection'  # Выбор услуги
    WAITING_SERVICES_ADD_MORE = 'waiting_services_add_more'  # Добавить еще или дальше


class UserState:
    """Класс для хранения состояния пользователя"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.state = State.START
        self.data = {}  # Данные регистрации
        self.temp = {}  # Временные данные встречи
        self.history = []  # История состояний
        self.previous_data = None  # Данные предыдущей встречи

    def set_state(self, new_state):
        """Установка нового состояния с сохранением в историю"""
        if self.state != new_state:
            self.history.append(self.state)
            self.state = new_state
            logger.info(f"User {self.user_id}: {self.state.value}")

    def go_back(self):
        """Возврат на предыдущее состояние"""
        if self.history:
            self.state = self.history.pop()
            logger.info(f"User {self.user_id}: back to {self.state.value}")
            return True
        return False

    def clear_temp(self):
        """Очистка временных данных"""
        self.temp = {}
        self.previous_data = None

    def clear_services(self):
        """Очистка списка услуг"""
        if 'services_list' in self.temp:
            del self.temp['services_list']

    def add_service(self, service):
        """Добавляет услугу в список"""
        if 'services_list' not in self.temp:
            self.temp['services_list'] = []
        if service not in self.temp['services_list']:
            self.temp['services_list'].append(service)
            logger.info(f"Добавлена услуга: {service}, список: {self.temp['services_list']}")

    def get_services_string(self):
        """Возвращает строку со всеми услугами"""
        if 'services_list' in self.temp and self.temp['services_list']:
            return ', '.join(self.temp['services_list'])
        return ''
