from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import create_main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Упрощенное главное меню без статистики
    """
    user = update.message.from_user

    welcome_text = f"""
Привет, {user.first_name}! 👋

Я - демо-бот для проверки знаний QA. 

Проверьте свои знания в области тестирования программного обеспечения и узнайте что-то новое!

📚 Что вас ждет:
• 5 вопросов по основам QA
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


def get_feedback(score, total):
    """
    Возвращает текст обратной связи в зависимости от результата
    """
    percentage = score / total
    if percentage >= 0.8:
        return "Отличный результат! Вы хорошо разбираетесь в основах QA!"
    elif percentage >= 0.6:
        return "Хороший результат! Продолжайте изучать материалы!"
    else:
        return "Есть над чем поработать! Рекомендуем изучить основы тестирования."
