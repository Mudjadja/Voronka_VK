# database.py
import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from config import DATA_DIR, SHEET_REG, SHEET_MEETINGS

logger = logging.getLogger(__name__)


class Database:
    """Работа с Excel файлами"""

    def __init__(self):
        self.ensure_directories()

    def ensure_directories(self):
        """Создает папки для Excel файлов"""
        DATA_DIR.mkdir(exist_ok=True)

    def get_excel_path(self, macro_region):
        """Путь к Excel файлу для макрорегиона"""
        safe_name = macro_region.replace(' ', '_')
        return DATA_DIR / safe_name / f'Voronka_{safe_name}.xlsx'

    def ensure_excel_file(self, macro_region):
        """Создает Excel файл если не существует"""
        excel_path = self.get_excel_path(macro_region)
        excel_path.parent.mkdir(parents=True, exist_ok=True)

        if not excel_path.exists():
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Лист регистрации
                df_reg = pd.DataFrame(columns=[
                    'Дата регистрации', 'ФИО', 'МРФ', 'РФ', 'Username', 'ID мессенджера'
                ])
                df_reg.to_excel(writer, sheet_name=SHEET_REG, index=False)

                # Лист данных по встречам
                df_meetings = pd.DataFrame(columns=[
                    'Клиент', 'ИНН', 'Контакт ФИО', 'Контакт номер',
                    'Повторная встреча?', 'Пользуется услугами', 'Услуги конкурентов',
                    'Новые услуги РТК (согл)', 'Информация по новым услугам РТК (подкл)',
                    'Рекомендации', 'Контакты рекомендации', 'Договоренности',
                    'Резюме встречи', 'Фото с клиентом', 'Регион',
                    'Время внесения по UTC', 'Имя при регистрации', 'ID мессенджера'
                ])
                df_meetings.to_excel(writer, sheet_name=SHEET_MEETINGS, index=False)

            logger.info(f"Создан файл {excel_path}")

    def get_user(self, user_id, macro_region=None):
        """Получает данные пользователя"""
        if macro_region:
            return self._get_user_from_file(user_id, macro_region)

        # Ищем во всех регионах
        from config import MACRO_REGIONS
        for region in MACRO_REGIONS.values():
            user = self._get_user_from_file(user_id, region)
            if user:
                return user
        return None

    def _get_user_from_file(self, user_id, macro_region):
        """Получает пользователя из конкретного файла"""
        excel_path = self.get_excel_path(macro_region)
        if not excel_path.exists():
            return None

        try:
            df = pd.read_excel(excel_path, sheet_name=SHEET_REG)
            user_row = df[df['ID мессенджера'].astype(str) == str(user_id)]
            if not user_row.empty:
                data = user_row.iloc[-1].to_dict()
                return {
                    'name': data.get('ФИО', ''),
                    'macro_region': data.get('МРФ', ''),
                    'subregion': data.get('РФ', ''),
                    'username': data.get('Username', ''),
                    'user_id': str(data.get('ID мессенджера', ''))
                }
        except Exception as e:
            logger.error(f"Ошибка чтения пользователя: {e}")
        return None

    def save_registration(self, user_data, macro_region, subregion):
        """Сохраняет регистрацию"""
        self.ensure_excel_file(macro_region)
        excel_path = self.get_excel_path(macro_region)

        try:
            df = pd.read_excel(excel_path, sheet_name=SHEET_REG)
            new_row = pd.DataFrame([[
                user_data['date_reg'],
                user_data['name'],
                macro_region,
                subregion,
                user_data.get('username', ''),
                user_data['user_id']
            ]], columns=df.columns)

            df = pd.concat([df, new_row], ignore_index=True)

            with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=SHEET_REG, index=False)

            logger.info(f"Сохранена регистрация {user_data['user_id']} в {macro_region}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False

    def find_previous_meeting(self, inn, macro_region):
        """Находит предыдущую встречу по ИНН"""
        excel_path = self.get_excel_path(macro_region)
        if not excel_path.exists():
            return None

        try:
            df = pd.read_excel(excel_path, sheet_name=SHEET_MEETINGS)
            if 'ИНН' in df.columns and not df.empty:
                prev = df[df['ИНН'].astype(str) == str(inn)]
                if not prev.empty:
                    return prev.iloc[-1].to_dict()
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
        return None

    def save_meeting(self, user_data, meeting_data, macro_region, subregion):
        """Сохраняет данные встречи (всегда новая строка)"""
        self.ensure_excel_file(macro_region)
        excel_path = self.get_excel_path(macro_region)

        try:
            df = pd.read_excel(excel_path, sheet_name=SHEET_MEETINGS)

            # Создаем новую строку с данными
            new_row = pd.DataFrame([[
                meeting_data.get('client', ''),
                meeting_data.get('inn', ''),
                meeting_data.get('contact_name', ''),
                meeting_data.get('contact_phone', ''),
                meeting_data.get('second_meeting', ''),
                meeting_data.get('competitors_use', ''),
                meeting_data.get('competitors_services', ''),
                meeting_data.get('consent_connect', ''),
                meeting_data.get('services_connect', ''),
                meeting_data.get('client_feedback', ''),
                meeting_data.get('feedback_contact', ''),
                meeting_data.get('agreement', ''),
                meeting_data.get('summary', ''),
                meeting_data.get('foto', ''),
                subregion,
                meeting_data.get('date_today', ''),
                user_data.get('name', ''),
                user_data.get('user_id', '')
            ]], columns=df.columns)

            # Добавляем строку в конец
            df = pd.concat([df, new_row], ignore_index=True)

            # Сохраняем
            with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=SHEET_MEETINGS, index=False)

            logger.info(f"Сохранена новая встреча в {macro_region}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False

