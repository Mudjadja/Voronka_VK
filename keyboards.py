# keyboards.py
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import MACRO_REGIONS, SUBREGIONS


class Keyboards:
    """Класс для создания клавиатур"""

    @staticmethod
    def get_start_keyboard():
        """Главное меню"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Ввести данные по встрече', color=VkKeyboardColor.POSITIVE)
        return keyboard

    @staticmethod
    def get_macro_regions_keyboard():
        """Выбор макрорегиона - по 2 кнопки в ряд"""
        keyboard = VkKeyboard(one_time=False)
        regions = list(MACRO_REGIONS.values())

        # Добавляем регионы по 2 в строку
        for i in range(0, len(regions), 2):
            keyboard.add_button(regions[i], color=VkKeyboardColor.PRIMARY)
            if i + 1 < len(regions):
                keyboard.add_button(regions[i + 1], color=VkKeyboardColor.PRIMARY)
            if i + 2 < len(regions):
                keyboard.add_line()

        return keyboard

    @staticmethod
    def get_subregions_keyboard(macro_region):
        """Выбор подрегиона - по 2 кнопки в ряд"""
        keyboard = VkKeyboard(one_time=False)
        subregions = SUBREGIONS.get(macro_region, [])

        # Добавляем подрегионы по 2 в строку
        for i in range(0, len(subregions), 2):
            keyboard.add_button(subregions[i], color=VkKeyboardColor.PRIMARY)
            if i + 1 < len(subregions):
                keyboard.add_button(subregions[i + 1], color=VkKeyboardColor.PRIMARY)
            if i + 2 < len(subregions):
                keyboard.add_line()

        return keyboard

    @staticmethod
    def get_yes_no_keyboard():
        """Да/Нет"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_back_keyboard():
        """Только назад"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_continue_keyboard():
        """Продолжить/Назад"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Продолжить', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_previous_choice_keyboard():
        """Клавиатура для выбора после предыдущей встречи"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Продолжить ввод', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Использовать предыдущие', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_services_keyboard():
        """Клавиатура с выбором услуг"""
        from config import SERVICES_LIST

        keyboard = VkKeyboard(one_time=False)

        # Добавляем услуги по 2 в ряд
        for i in range(0, len(SERVICES_LIST), 2):
            keyboard.add_button(SERVICES_LIST[i], color=VkKeyboardColor.PRIMARY)
            if i + 1 < len(SERVICES_LIST):
                keyboard.add_button(SERVICES_LIST[i + 1], color=VkKeyboardColor.PRIMARY)
            if i + 2 < len(SERVICES_LIST):
                keyboard.add_line()

        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard

    @staticmethod
    def get_services_add_more_keyboard():
        """Клавиатура для добавления услуг или завершения"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('➕ Добавить услугу', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('➡️ Дальше', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
        return keyboard