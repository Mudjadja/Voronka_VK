# utils.py
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Utils:
    """Вспомогательные функции"""

    @staticmethod
    def get_user_info(vk, user_id):
        """Получение информации о пользователе VK"""
        try:
            users = vk.users.get(user_ids=user_id, fields='first_name,last_name,screen_name')
            if users:
                user = users[0]
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()
                username = user.get('screen_name', '')

                return full_name, username
        except Exception as e:
            logger.error(f"Ошибка получения информации пользователя: {e}")

        return "Неизвестно", ""

    @staticmethod
    def get_timezone_for_region(subregion):
        """Получает часовой пояс для подрегиона"""
        from config import TIMEZONES
        return TIMEZONES.get(subregion, 3)  # По умолчанию Москва

    @staticmethod
    def get_current_time_utc():
        """Получает текущее время в UTC"""
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def copy_previous_data(previous_data):
        """Копирует данные из предыдущей встречи"""
        return {
            'client': previous_data.get('Клиент', ''),
            'inn': previous_data.get('ИНН', ''),
            'contact_name': previous_data.get('Контакта ФИО', ''),
            'contact_telefon': previous_data.get('Контакт номер', ''),
            'second_meeting': 'Да',
            'competitors_services_use': previous_data.get('Пользуется услугами', ''),
            'competitors_services': previous_data.get('Услуги конкурентов', ''),
            'consent_connect': previous_data.get('Новые услуги РТК (согл)', ''),
            'services_connect': previous_data.get('Информация по новым услугам РТК (подкл)', ''),
            'client_feedback': previous_data.get('Рекомендации', ''),
            'client_feedback_contact': previous_data.get('Контакты рекомендации', ''),
            'agreement_second_meeting': previous_data.get('Договоренности', ''),
            'meeting_summary': previous_data.get('Резюме встречи', ''),
            'foto': 'скопировано из предыдущей встречи'
        }