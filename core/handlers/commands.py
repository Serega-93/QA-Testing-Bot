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

    # ОТЛАДКА: выводим все данные
    from data.storage import storage
    storage.debug_print_all_data()

    # Получаем статистику
    stats = StatsService.get_user_stats(user.id)
    success_rate = StatsService.calculate_success_rate(stats)

    # Формируем блок статистики
    if stats and stats.total_tests > 0:
        stats_section = f"""
📊 Ваша статистика:
🎯 Тестов пройдено: {stats.total_tests}
🏆 Лучший результат: {stats.best_score}/30
📈 Успешность: {success_rate}%
"""
    else:
        stats_section = "📊 Статистика: пройдите первый тест!"

    welcome_text = f"""
Привет, {user.first_name}! 👋

Я - демо-бот для проверки знаний QA. 

{stats_section}

📚 Что вас ждет:
• 30 вопросов по основам QA
• Подробные объяснения к каждому ответу
• Статистика ваших результатов

Готовы начать? 🚀
    """

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
