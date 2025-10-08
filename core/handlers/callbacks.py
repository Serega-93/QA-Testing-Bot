from telegram import Update
from telegram.ext import ContextTypes
import asyncio

from utils.keyboards import create_main_menu_keyboard, create_stats_keyboard, create_quiz_keyboard
from core.services.quiz import QuizService

# Создаем экземпляр сервиса
quiz_service = QuizService()


async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главный обработчик нажатий на inline-кнопки
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    # Обработка разных типов кнопок
    if data == "cancel_test":
        await cancel_test_from_button(query, context)
    elif data == "restart_test":
        await restart_from_button(query, context)
    elif data == "restart_from_menu":
        await restart_from_menu_button(query, context)
    elif data == "show_stats_from_menu":
        await stats_from_menu(query, context)
    elif data == "start_test_from_menu":
        await start_test_from_menu(query, context)
    elif data == "main_menu":
        await main_menu(query, context)
    elif data.startswith("answer_"):
        await process_answer(query, data, context)


async def start_test_from_menu(query, context):
    """
    Начинает тест из главного меню
    """
    success = await quiz_service.start_quiz(context)

    if not success:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    await show_question_from_menu(query, context)


async def show_question_from_menu(query, context):
    """
    Показывает вопрос при старте из меню
    """
    result = await QuizService.get_current_question(context)

    if result is None:
        await finish_test_from_callback(query, context)
        return

    question, current_index = result

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(context.user_data['questions'])}
{question['question']}

""" + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(question['options'])])

    await query.edit_message_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index)
    )


async def cancel_test_from_button(query, context):
    """
    Отменяет текущий тест и возвращает в главное меню
    """
    # Очищаем данные теста
    for key in ['questions', 'current_question', 'score', 'last_question_message_id']:
        if key in context.user_data:
            del context.user_data[key]

    cancel_text = """
🚫 Тест отменен

Вы вернулись в главное меню.
"""

    await query.message.reply_text(cancel_text)
    await main_menu(query, context)


async def main_menu(query, context):
    """
    Возвращает в главное меню из любого места
    """
    user = query.from_user

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

    await query.edit_message_text(
        welcome_text,
        reply_markup=create_main_menu_keyboard()
    )


async def restart_from_button(query, context):
    """
    Перезапускает тест при нажатии на кнопку
    """
    # Очищаем только данные теста, оставляя вопросы
    questions = context.user_data.get('questions', [])
    for key in ['current_question', 'score', 'last_question_message_id']:
        if key in context.user_data:
            del context.user_data[key]

    # Восстанавливаем вопросы для нового теста
    if questions:
        context.user_data['questions'] = questions

    restart_text = """
🔄 Тест начат заново!

Все прогресс сброшен. Удачи! 🍀
    """

    # Редактируем сообщение с результатом
    await query.edit_message_text(restart_text, reply_markup=None)

    # Запускаем новый тест
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    # Показываем первый вопрос
    await show_question_from_menu(query, context)


async def restart_from_menu_button(query, context):
    """
    Перезапускает бота из главного меню
    """
    # Полностью очищаем все данные
    context.user_data.clear()

    restart_text = """
🔄 Бот перезапущен!

Все данные очищены. Вы начинаете с чистого листа.

Готовы к новым испытаниям? 🚀
    """

    # Показываем сообщение и возвращаем в главное меню
    await query.edit_message_text(restart_text, reply_markup=None)

    # Через секунду показываем главное меню
    await asyncio.sleep(1)
    await main_menu(query, context)


async def stats_from_menu(query, context):
    """
    Показывает статистику из главного меню
    """
    from core.handlers.commands import get_feedback  # временный импорт

    last_score = context.user_data.get('last_score')
    last_total = context.user_data.get('last_total')

    if last_score is None or last_total is None:
        stats_text = "📊 У вас пока нет результатов тестирования. Пройдите тест сначала!"
    else:
        percentage = round((last_score / last_total) * 100)
        stats_text = f"""
📊 Подробная статистика

🎯 Результат: {last_score}/{last_total} ({percentage}%)
📊 Процент правильных ответов: {percentage}%

{get_feedback(last_score, last_total)}
        """

    await query.edit_message_text(stats_text, reply_markup=create_stats_keyboard())


async def process_answer(query, data, context):
    """
    Обрабатывает ответ пользователя
    """
    # Разбираем callback_data: "answer_номер_вопроса_номер_ответа"
    parts = data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])

    # Обрабатываем ответ через сервис
    result_message, is_correct = await QuizService.process_answer(context, question_index, answer_index)

    # Отправляем сообщение с результатом
    await query.message.reply_text(result_message)

    # Проверяем, не закончился ли тест
    if QuizService.is_quiz_finished(context):
        await finish_test_from_callback(query, context)
        return

    # Ждем немного перед следующим вопросом
    await asyncio.sleep(1)

    # Показываем следующий вопрос
    await show_next_question(query, context)


async def show_next_question(query, context):
    """
    Показывает следующий вопрос
    """
    result = await QuizService.get_current_question(context)

    if result is None:
        await finish_test_from_callback(query, context)
        return

    question, current_index = result

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(context.user_data['questions'])}
{question['question']}

""" + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(question['options'])])

    # Отправляем новое сообщение с вопросом
    message = await query.message.reply_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index)
    )
    context.user_data['last_question_message_id'] = message.message_id


async def finish_test_from_callback(query, context):
    """
    Завершает тест при вызове из callback
    """
    from core.handlers.commands import get_feedback  # временный импорт
    from utils.keyboards import create_restart_keyboard

    score, total = QuizService.get_quiz_results(context)

    # Сохраняем статистику
    context.user_data['last_score'] = score
    context.user_data['last_total'] = total

    # Формируем текст результата
    result_text = f"""
🎉 Тест завершен!

📊 Ваш результат: {score}/{total}
💯 Процент правильных ответов: {round(score / total * 100)}%

{get_feedback(score, total)}
    """

    # Очищаем временные данные теста
    for key in ['current_question', 'score', 'last_question_message_id']:
        if key in context.user_data:
            del context.user_data[key]

    # Отправляем результат с кнопками
    await query.message.reply_text(result_text, reply_markup=create_restart_keyboard())
