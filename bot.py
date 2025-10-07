from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from database import load_questions
import asyncio
from datetime import datetime


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

    # Создаем клавиатуру для главного меню
    keyboard = [
        [InlineKeyboardButton("🎯 Начать тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats_from_menu")],
        [InlineKeyboardButton("🔄 Перезапустить бота", callback_data="restart_from_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


# Обработчик команды /test
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процесс тестирования
    """
    # Загружаем вопросы из JSON файла
    questions = load_questions()

    # Проверяем, есть ли вопросы
    if not questions:
        await update.message.reply_text("❌ Вопросы не найдены! Проверьте файл questions.json")
        return

    # Сохраняем вопросы в 'память' бота для этого пользователя
    context.user_data['questions'] = questions
    context.user_data['current_question'] = 0  # Индекс текущего вопроса
    context.user_data['score'] = 0  # Счетчик правильных ответов

    # Показываем первый вопрос
    await show_question(update, context)


# Обработчик команды /cancel
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команду /cancel - отменяет тест если он активен
    """
    if 'current_question' in context.user_data:
        await cancel_test(update, context)
    else:
        await update.message.reply_text("❌ Нечего отменять. Вы не в процессе тестирования.")


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

Доступные команды:
/start - Начало работы  
/test - Начать тестирование
/restart - Перезапустить бота

Готовы к новым испытаниям? 🚀
    """

    await update.message.reply_text(restart_text)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает подробную статистику пользователя
    """
    last_score = context.user_data.get('last_score')
    last_total = context.user_data.get('last_total')
    last_test_date = context.user_data.get('last_test_date')

    if last_score is None or last_total is None:
        stats_text = """
📊 Статистика

У вас пока нет результатов тестирования.

Пройдите тест командой /test чтобы увидеть свою статистику!
        """
    else:
        percentage = round((last_score / last_total) * 100)

        # Создаем визуальный прогресс-бар
        progress_bar = create_progress_bar(percentage)

        stats_text = f"""
📊 Подробная статистика

🎯 Последний результат: {last_score}/{last_total}
📈 Процент правильных ответов: {percentage}%
{progress_bar}
📅 Дата тестирования: {last_test_date}

{get_feedback(last_score, last_total)}

💡 Совет: Регулярное тестирование помогает закрепить знания!
        """

    # Клавиатура для действий
    keyboard = [
        [InlineKeyboardButton("🎯 Пройти тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(stats_text, reply_markup=reply_markup)


def create_progress_bar(percentage, length=10):
    """
    Создает визуальный прогресс-бар
    """
    filled = round((percentage / 100) * length)
    empty = length - filled
    return "🟩" * filled + "⬜" * empty + f" {percentage}%"


async def cancel_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отменяет текущий тест и возвращает в главное меню
    """
    # Очищаем данные теста
    if 'questions' in context.user_data:
        del context.user_data['questions']
    if 'current_question' in context.user_data:
        del context.user_data['current_question']
    if 'score' in context.user_data:
        del context.user_data['score']

    cancel_text = """
🚫 Тест отменен

Вы вернулись в главное меню.

Доступные команды:
/start - Начало работы
/test - Начать новый тест

Не сдавайтесь! Каждая попытка - это шаг к успеху! 💪
    """

    # Отправляем сообщение без клавиатуры (возврат к обычному чату)
    await update.message.reply_text(cancel_text, reply_markup=None)


# Функция для отображения вопроса
async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает первый вопрос
    """
    questions = context.user_data['questions']
    current_index = context.user_data['current_question']

    if current_index >= len(questions):
        await finish_test(update, context)
        return

    question = questions[current_index]

    # Создаем inline-кнопки
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        for j in range(2):
            if i + j < len(question['options']):
                callback_data = f"answer_{current_index}_{i + j}"
                row.append(InlineKeyboardButton(
                    f"{i + j + 1}",
                    callback_data=callback_data
                ))
        if row:
            keyboard.append(row)

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel_test")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем чистый текст вопроса
    options_text = ""
    for i, option in enumerate(question['options']):
        options_text += f"\n{i + 1}. {option}"

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(questions)}
{question['question']}

{options_text}
"""

    # Отправляем новое сообщение
    message = await update.message.reply_text(question_text, reply_markup=reply_markup)
    context.user_data['last_question_message_id'] = message.message_id


async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает нажатия на inline-кнопки
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
    # Используем ту же логику, что и в stats_command
    last_score = context.user_data.get('last_score')
    last_total = context.user_data.get('last_total')
    last_test_date = context.user_data.get('last_test_date')

    if last_score is None or last_total is None:
        stats_text = "📊 У вас пока нет результатов тестирования. Пройдите тест сначала!"
    else:
        percentage = round((last_score / last_total) * 100)
        progress_bar = create_progress_bar(percentage)

        stats_text = f"""
📊 Подробная статистика

🎯 Результат: {last_score}/{last_total} ({percentage}%)
{progress_bar}
📅 Дата: {last_test_date}

{get_feedback(last_score, last_total)}
        """

    keyboard = [
        [InlineKeyboardButton("🎯 Пройти тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(stats_text, reply_markup=reply_markup)


async def start_test_from_menu(query, context):
    """
    Начинает тест из главного меню
    """
    questions = load_questions()

    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    # Инициализируем тест
    context.user_data['questions'] = questions
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    # Показываем первый вопрос
    await show_question_from_menu(query, context)


async def show_question_from_menu(query, context):
    """
    Показывает вопрос при старте из меню
    """
    questions = context.user_data['questions']
    current_index = context.user_data['current_question']

    question = questions[current_index]

    # Создаем inline-кнопки с группировкой по 2 в ряд
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        for j in range(2):
            if i + j < len(question['options']):
                callback_data = f"answer_{current_index}_{i + j}"
                row.append(InlineKeyboardButton(
                    f"{i + j + 1}",
                    callback_data=callback_data
                ))
        if row:
            keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel_test")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем текст вопроса
    options_text = ""
    for i, option in enumerate(question['options']):
        options_text += f"\n{i + 1}. {option}"

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(questions)}
{question['question']}

{options_text}
"""

    await query.edit_message_text(question_text, reply_markup=reply_markup)


async def main_menu(query, context):
    """
    Возвращает в упрощенное главное меню
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

    # Создаем клавиатуру для главного меню
    keyboard = [
        [InlineKeyboardButton("🎯 Начать тест", callback_data="start_test_from_menu")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats_from_menu")],
        [InlineKeyboardButton("🔄 Перезапустить бота", callback_data="restart_from_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(welcome_text, reply_markup=reply_markup)


async def restart_from_button(query, context):
    """
    Перезапускает тест при нажатии на кнопку
    """
    # Очищаем только данные теста, оставляя вопросы
    questions = context.user_data.get('questions', [])
    context.user_data.clear()

    # Восстанавливаем вопросы для нового теста
    if questions:
        context.user_data['questions'] = questions

    restart_text = """
🔄 Тест начат заново!

Весь прогресс сброшен.\nУдачи! 🍀
    """

    # Редактируем сообщение с результатом
    await query.edit_message_text(restart_text, reply_markup=None)

    # Запускаем новый тест
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    # Показываем первый вопрос
    await show_question_from_restart(query, context)


async def show_stats_from_button(query, context):
    """
    Показывает статистику пользователя
    """
    last_score = context.user_data.get('last_score', 0)
    total_questions = len(context.user_data.get('questions', []))

    if total_questions == 0:
        stats_text = "📊 Статистика пока недоступна. Пройдите тест сначала!"
    else:
        percentage = round((last_score / total_questions) * 100)
        stats_text = f"""
📊 Ваша статистика:

🎯 Последний результат: {last_score}/{total_questions}
📈 Процент правильных ответов: {percentage}%

{get_feedback(last_score, total_questions)}
        """

    # Клавиатура для возврата
    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data="restart_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(stats_text, reply_markup=reply_markup)


async def show_question_from_restart(query, context):
    """
    Показывает вопрос после перезапуска теста с правильной группировкой кнопок
    """
    questions = context.user_data['questions']
    current_index = context.user_data['current_question']

    question = questions[current_index]

    # Создаем inline-кнопки с группировкой по 2 в ряд
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        for j in range(2):
            if i + j < len(question['options']):
                callback_data = f"answer_{current_index}_{i + j}"
                row.append(InlineKeyboardButton(
                    f"{i + j + 1}",
                    callback_data=callback_data
                ))
        if row:
            keyboard.append(row)

    # Добавляем кнопку отмены в отдельный ряд
    keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel_test")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем текст вопроса
    options_text = ""
    for i, option in enumerate(question['options']):
        options_text += f"\n{i + 1}. {option}"

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(questions)}
{question['question']}

{options_text}
"""

    # Отправляем новое сообщение
    await query.message.reply_text(question_text, reply_markup=reply_markup)


async def cancel_test_from_button(query, context):
    """
    Отменяет тест при нажатии на inline-кнопку
    """
    # Очищаем данные теста
    if 'questions' in context.user_data:
        del context.user_data['questions']
    if 'current_question' in context.user_data:
        del context.user_data['current_question']
    if 'score' in context.user_data:
        del context.user_data['score']
    if 'last_question_message_id' in context.user_data:
        del context.user_data['last_question_message_id']

    cancel_text = """
🚫 Тест отменен

Вы вернулись в главное меню.

Доступные команды:
/start - Начало работы
/test - Начать новый тест

Не сдавайтесь! Каждая попытка - это шаг к успеху! 💪
    """

    # Редактируем сообщение с вопросом
    await query.edit_message_text(cancel_text, reply_markup=None)


async def process_answer(query, data, context):
    """
    Обрабатывает ответ пользователя с минималистичным результатом
    """
    parts = data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])

    questions = context.user_data['questions']
    current_question = questions[question_index]

    # Проверяем правильность ответа
    if answer_index == current_question['correct_answer']:
        context.user_data['score'] += 1
        result_icon = "✅"
        result_text = "Правильно!"
    else:
        result_icon = "❌"
        result_text = f"Не правильно!"

    # Минималистичное сообщение с результатом
    result_message = f"""Вопрос {question_index + 1}: {result_icon}\n{result_text}

💡 {current_question['explanation']}"""

    # Отправляем компактное сообщение с результатом
    await query.message.reply_text(result_message)

    # Переходим к следующему вопросу
    context.user_data['current_question'] = question_index + 1

    # Проверяем, не закончился ли тест
    if context.user_data['current_question'] >= len(questions):
        await finish_test_from_callback(query, context)
        return

    # Ждем немного перед следующим вопросом
    await asyncio.sleep(1)

    # Показываем следующий вопрос
    await show_next_question(query, context)


async def show_next_question(query, context):
    """
    Показывает следующий вопрос как новое сообщение
    """
    questions = context.user_data['questions']
    current_index = context.user_data['current_question']

    question = questions[current_index]

    # Создаем inline-кнопки
    keyboard = []
    for i in range(0, len(question['options']), 2):
        row = []
        for j in range(2):
            if i + j < len(question['options']):
                callback_data = f"answer_{current_index}_{i + j}"
                row.append(InlineKeyboardButton(
                    f"{i + j + 1}",
                    callback_data=callback_data
                ))
        if row:
            keyboard.append(row)

    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("🚫 Отмена", callback_data="cancel_test")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Формируем чистый текст вопроса
    options_text = ""
    for i, option in enumerate(question['options']):
        options_text += f"\n{i + 1}. {option}"

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(questions)}
{question['question']}

{options_text}
"""

    # Отправляем новое сообщение с вопросом
    message = await query.message.reply_text(question_text, reply_markup=reply_markup)
    context.user_data['last_question_message_id'] = message.message_id


async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает результаты теста с кнопками перезапуска и главного меню
    """
    score = context.user_data['score']
    total = len(context.user_data['questions'])

    # Сохраняем статистику
    context.user_data['last_score'] = score
    context.user_data['last_total'] = total
    context.user_data['last_test_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Формируем текст результата
    result_text = f"""
🎉 Тест завершен!

📊 Ваш результат: {score}/{total}
💯 Процент правильных ответов: {round(score / total * 100)}%

{get_feedback(score, total)}
    """

    # Кнопки перезапуска и главного меню
    keyboard = [
        [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_test")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Очищаем временные данные теста
    if 'current_question' in context.user_data:
        del context.user_data['current_question']
    if 'score' in context.user_data:
        del context.user_data['score']
    if 'last_question_message_id' in context.user_data:
        del context.user_data['last_question_message_id']

    # Отправляем результат
    await update.message.reply_text(result_text, reply_markup=reply_markup)


async def finish_test_from_callback(query, context):
    """
    Завершает тест при вызове из callback с кнопками перезапуска и главного меню
    """
    score = context.user_data['score']
    total = len(context.user_data['questions'])

    # Сохраняем статистику
    context.user_data['last_score'] = score
    context.user_data['last_total'] = total
    context.user_data['last_test_date'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Формируем текст результата
    result_text = f"""
🎉 Тест завершен!

📊 Ваш результат: {score}/{total}
💯 Процент правильных ответов: {round(score / total * 100)}%

{get_feedback(score, total)}
    """

    # Кнопки перезапуска и главного меню
    keyboard = [
        [InlineKeyboardButton("🔄 Начать заново", callback_data="restart_test")],
        [InlineKeyboardButton("📋 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Очищаем временные данные теста
    if 'current_question' in context.user_data:
        del context.user_data['current_question']
    if 'score' in context.user_data:
        del context.user_data['score']
    if 'last_question_message_id' in context.user_data:
        del context.user_data['last_question_message_id']

    # Отправляем результат с кнопками
    await query.message.reply_text(result_text, reply_markup=reply_markup)


# Вспомогательная функция для фидбэка
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


# Главная функция запуска бота
def main():
    """
    Основная функция которая запускает бота
    """
    print("🚀 Запускаю QA Testing Bot...")

    # Создаем приложение бота с нашим токеном
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Регистрируем обработчик нажатий на inline-кнопки
    application.add_handler(CallbackQueryHandler(handle_button_click))

    print("✅ Бот запущен и готов к работе!")
    print("⏹️  Для остановки нажмите Ctrl+C")

    # Запускаем бота в режиме опроса (polling)
    application.run_polling()


# Точка входа в программу
if __name__ == "__main__":
    main()