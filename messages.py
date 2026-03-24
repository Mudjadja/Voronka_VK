# messages.py
from datetime import datetime


class Messages:
    """Тексты сообщений"""

    @staticmethod
    def welcome_back(name, region):
        return f"С возвращением, {name}!\nВаш регион: {region}"

    @staticmethod
    def ask_fio():
        return "Пожалуйста, укажите ваши ФИО:"

    @staticmethod
    def ask_macro_region():
        return "Выберите макрорегион:"

    @staticmethod
    def ask_subregion(macro):
        return f"Выберите регион в {macro}:"

    @staticmethod
    def registration_complete(name):
        return f"Регистрация завершена, {name}!"

    @staticmethod
    def main_menu():
        return "Нажмите кнопку для ввода данных:"

    @staticmethod
    def ask_client():
        return "Введи название компании с кем прошла встреча:"

    @staticmethod
    def ask_inn():
        return "Введи ИНН компании:"

    @staticmethod
    def ask_second_meeting():
        return "Встреча повторная?"

    @staticmethod
    def ask_contact_name():
        return "Введи ФИО того, с кем состоялась встреча:"

    @staticmethod
    def ask_contact_phone():
        return "Введи номер телефона того, с кем состоялась встреча:"

    @staticmethod
    def ask_competitors_use():
        return "Пользуется ли клиент услугами конкурентов?"

    @staticmethod
    def ask_competitors_services():
        return "Напиши одним сообщением, какими услугами пользуется у конкурентов и условия:"

    @staticmethod
    def ask_consent_connect():
        return "Получили ли согласие на подключение новых услуг РТК?"

    @staticmethod
    def ask_services_connect():
        return "Напиши одним сообщением, какие услуги и параметры (услуга, кол-во, скорость и пр.)?"

    @staticmethod
    def ask_client_feedback():
        return "Есть ли рекомендации от клиента?"

    @staticmethod
    def ask_feedback_contact():
        return "Напиши, Компанию, ФИО и контакты, кого порекомендовал клиент:"

    @staticmethod
    def ask_agreement():
        return "Есть ли договоренности с клиентом на повторную встречу или звонок?"

    @staticmethod
    def ask_summary():
        return "Напиши краткое резюме встречи с клиентом:"

    @staticmethod
    def ask_photo():
        return "Добавь фото с клиентом (отправьте фото или напишите 'нет фото'):"

    @staticmethod
    def save_success():
        return "✅ Данные встречи сохранены!"

    @staticmethod
    def format_previous_meeting(data):
        """Форматирует информацию о предыдущей встрече"""
        info = "📋 Информация о последней встрече:\n\n"
        info += f"🏢 Компания: {data.get('Клиент', 'Не указано')}\n"
        info += f"🔢 ИНН: {data.get('ИНН', 'Не указано')}\n"

        date = data.get('Время внесения по UTC', 'Не указано')
        if isinstance(date, datetime):
            date = date.strftime('%d.%m.%Y %H:%M')
        info += f"📅 Дата: {date}\n"

        info += f"👤 Контакт: {data.get('Контакт ФИО', 'Не указано')}\n"
        info += f"📞 Телефон: {data.get('Контакт номер', 'Не указано')}\n"
        info += f"⚡ Услуги конкурентов: {data.get('Услуги конкурентов', 'Не указано')}\n"
        info += f"📊 Новые услуги РТК: {data.get('Информация по новым услугам РТК (подкл)', 'Не указано')}\n"
        info += f"👥 Контакты рекомендации: {data.get('Контакты рекомендации', 'Не указано')}\n"
        info += f"📝 Резюме встречи: {data.get('Резюме встречи', 'Не указано')}"

        # Если есть фото, добавляем информацию о нем
        foto = data.get('Фото с клиентом', '')
        if foto and foto != 'нет фото' and 'jpg' in foto:
            info += f"\n\n📸 Фото: {foto}"

        return info

    @staticmethod
    def copy_success(client, inn, date):
        """Сообщение об успешном копировании"""
        return (f"✅ Данные скопированы из предыдущей встречи и сохранены!\n"
                f"📅 Дата встречи: {date}\n"
                f"🏢 Клиент: {client}\n"
                f"🔢 ИНН: {inn}")

    @staticmethod
    def ask_services_selection():
        return "Выберите услугу:"

    @staticmethod
    def service_added(service):
        return f"✅ Добавлена услуга: {service}\n\nМожешь добавить ещё или перейти дальше."

    @staticmethod
    def no_services_selected():
        return "⚠️ Вы не выбрали ни одной услуги. Продолжить?"