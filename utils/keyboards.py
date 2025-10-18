from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random


def create_quiz_keyboard(question, current_index, shuffled_options=None):
    """
    Создает клавиатуру для вопроса теста
    """
    # Используем перемешанные варианты если они есть, иначе оригинальные
    options = shuffled_options if shuffled_options else question['options']

    # Создаем inline-кнопки с группировкой по 2 в ряд
    keyboard = []
    for i in range(0, len(options), 2):
        row = []
        for j in range(2):
            if i + j < len(options):
                callback_data = f"answer_{current_index}_{i + j}"
                row.append(InlineKeyboardButton(
                    f"{i + j + 1}",
                    callback_data=callback_data
                ))
        if row:
            keyboard.append(row)

    # Добавляем кнопку отмены в отдельный ряд
    keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel_test")])

    return InlineKeyboardMarkup(keyboard)


def create_main_menu_keyboard():
    """
    Создает клавиатуру главного меню
    """
    keyboard = [
        [InlineKeyboardButton("🎯 Начать тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("🗑️ Сбросить статистику", callback_data="reset_stats_confirm")],
        [InlineKeyboardButton("🔄 Перезапустить бота", callback_data="restart_from_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_confirmation_keyboard():
    """
    Создает клавиатуру для подтверждения опасных действий
    """
    keyboard = [
        [InlineKeyboardButton("✅ Да, сбросить", callback_data="reset_stats_yes")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data="reset_stats_no")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_restart_keyboard():
    """
    Создает клавиатуру после завершения теста
    """
    keyboard = [
        [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_test")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_level_selection_keyboard():
    """
    Создает клавиатуру для выбора уровня сложности
    """
    keyboard = [
        [InlineKeyboardButton("🎓 Junior", callback_data="level_junior")],
        [InlineKeyboardButton("💪 Middle", callback_data="level_middle")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_stats_keyboard():
    """
    Создает клавиатуру для страницы статистики
    """
    keyboard = [
        [InlineKeyboardButton("🎯 Пройти тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
