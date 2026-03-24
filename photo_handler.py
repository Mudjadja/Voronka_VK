# photo_handler.py
import requests
import logging
import re
from datetime import datetime
from pathlib import Path
from config import PHOTOS_DIR

logger = logging.getLogger(__name__)


class PhotoHandler:
    """Работа с фотографиями"""

    def __init__(self, vk):
        self.vk = vk

    def get_photo_url(self, event):
        """Получает URL фото из сообщения"""
        try:
            messages = self.vk.messages.getById(message_ids=event.message_id)
            if not messages or 'items' not in messages:
                return None

            attachments = messages['items'][0].get('attachments', [])
            for att in attachments:
                if att['type'] == 'photo':
                    photo = att['photo']
                    sizes = photo.get('sizes', [])
                    if sizes:
                        # Берем самое большое фото
                        max_size = max(sizes, key=lambda x: x.get('height', 0) * x.get('width', 0))
                        return max_size.get('url', '')

                    # Альтернативный способ
                    for key in ['photo_2560', 'photo_1280', 'photo_807', 'photo_604', 'photo_130']:
                        if key in photo:
                            return photo[key]
        except Exception as e:
            logger.error(f"Ошибка получения фото: {e}")
        return None

    def save_photo(self, photo_url, macro_region, client_name, inn, manager_name):
        """
        Сохраняет фото в папку макрорегиона
        Возвращает только имя файла (без пути)
        """
        try:
            # Очищаем имя файла
            def clean(text):
                # Удаляем недопустимые символы
                cleaned = re.sub(r'[\\/*?:"<>|]', '_', str(text))
                # Обрезаем длинные имена
                return cleaned[:50]

            # Формируем имя файла: дата_название клиента_ИНН_Имя менеджера
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{date_str}_{clean(client_name)}_{clean(inn)}_{clean(manager_name)}.jpg"

            # Папка макрорегиона
            region_dir = PHOTOS_DIR / macro_region.replace(' ', '_')
            region_dir.mkdir(parents=True, exist_ok=True)

            filepath = region_dir / filename

            # Скачиваем фото
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(photo_url, stream=True, timeout=10, headers=headers)

            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                # Проверяем размер файла
                if filepath.stat().st_size > 0:
                    logger.info(f"Фото сохранено: {filepath}")
                    # Возвращаем только имя файла
                    return filename
                else:
                    # Удаляем пустой файл
                    filepath.unlink()
                    logger.error("Файл пустой, удален")
                    return None
            else:
                logger.error(f"Ошибка скачивания: статус {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Ошибка сохранения фото: {e}")
            return None