from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import create_main_menu_keyboard
from core.services.stats import StatsService
from utils.feedback import get_feedback


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главное меню СО статистикой пользователя
    """
    user = update.message.from_user

    # Инициализируем пользователя в системе
    StatsService.init_user(user.id, user.username, user.first_name)

    # Получаем статистику
    stats = StatsService.get_user_stats(user.id)

    # Формируем блоки статистики для каждого уровня
    junior_stats = ""
    middle_stats = ""

    if stats and (stats.junior_tests > 0 or stats.middle_tests > 0):
        if stats.junior_tests > 0:
            junior_success = StatsService.calculate_level_success_rate(stats, "junior")
            junior_stats = f"""👶 Junior:
    • Тестов: {stats.junior_tests}
    • Правильных ответов: {stats.junior_total_correct}/{stats.junior_total_questions}
    • Успешность: {junior_success}%"""

        if stats.middle_tests > 0:
            middle_success = StatsService.calculate_level_success_rate(stats, "middle")
            middle_stats = f"""💪 Middle:
    • Тестов: {stats.middle_tests}  
    • Лучший результат: {stats.middle_best_score}/100
    • Успешность: {middle_success}%"""

        # Правильное объединение с одним отступом
        if junior_stats and middle_stats:
            stats_section = f"""📊 Ваша статистика:

    {junior_stats}

    {middle_stats}"""
        else:
            stats_section = f"""📊 Ваша статистика:

    {junior_stats}{middle_stats}"""
    else:
        stats_section = "📊 Статистика: пройдите первый тест!"

    welcome_text = f"""Привет, {user.first_name}! 👋

Я бот для проверки знаний QA.

{stats_section}

📚 Что вас ждет:
• 100 вопросов по основам QA
• Подробные объяснения к каждому ответу
• Статистика ваших результатов

Готовы начать? 🚀"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=create_main_menu_keyboard()
    )


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Полностью перезапускает бота - очищает все данные и начинает с начала
    """
    # Полностью очищаем все данные пользователя
    context.user_data.clear()

    user = update.message.from_user

    restart_text = f"""
🔄 Бот перезапущен!

Привет снова, {user.first_name}! 👋

Все данные очищены. Вы начинаете с чистого листа.

Готовы к новым испытаниям? 🚀
    """

    await update.message.reply_text(restart_text)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду /cancel - отменяет тест если он активен
    """
    if 'current_question' in context.user_data:
        from core.handlers.callbacks import cancel_test_from_button
        # Создаем fake query для совместимости
        class FakeQuery:
            def __init__(self, message):
                self.message = message

        fake_query = FakeQuery(update.message)
        await cancel_test_from_button(fake_query, context)
    else:
        await update.message.reply_text("❌ Нечего отменять. Вы не в процессе тестирования.")
