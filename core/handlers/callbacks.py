from telegram import Update
from telegram.ext import ContextTypes
import asyncio
from utils.feedback import get_feedback
from utils.keyboards import create_main_menu_keyboard, create_quiz_keyboard
from core.services.quiz import QuizService
from core.services.stats import StatsService
from data.database import load_questions


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
    elif data == "level_junior":
        await start_junior_quiz(query, context)
    elif data == "level_middle":
        await start_middle_quiz(query, context)
    elif data == "main_menu":
        await main_menu(query, context)
    elif data == "reset_stats_confirm":
        await confirm_reset_stats(query, context)
    elif data == "reset_stats_yes":
        await reset_stats(query, context)
    elif data == "reset_stats_no":
        await main_menu(query, context)
    elif data.startswith("answer_"):
        await process_answer(query, data, context)


async def start_test_from_menu(query, context):
    """
    Показывает выбор уровня сложности перед началом теста
    """
    from utils.keyboards import create_level_selection_keyboard

    level_selection_text = """
🎯 Выберите уровень сложности:

👶 Junior
• Неограниченные попытки
• Подходит для начинающих

💪 Middle
• 1 попытка на вопрос
• Ошибка = конец теста
• Для проверки реальных знаний!

Выберите уровень:
    """

    await query.edit_message_text(
        level_selection_text,
        reply_markup=create_level_selection_keyboard()
    )


async def start_junior_quiz(query, context):
    """
    Начинает тест в режиме Junior (неограниченные попытки)
    """
    questions = load_questions()
    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    context.user_data.update({
        'questions': questions,
        'current_question': 0,
        'score': 0,
        'level': 'junior'
    })

    junior_text = """
👶 Режим: Junior

Учитесь в своем темпе! Ошибаться - это нормально! 📚

Удачи! 🍀
    """

    await query.edit_message_text(junior_text)
    await show_question_from_menu(query, context)


async def start_middle_quiz(query, context):
    """
    Начинает тест в режиме Middle (1 попытка на вопрос)
    """
    questions = load_questions()
    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    context.user_data.update({
        'questions': questions,
        'current_question': 0,
        'score': 0,
        'level': 'middle'
    })

    middle_text = """
💪 Режим: Middle

Всего 1 попытка на вопрос! Ошибка = конец теста! ⚡

Покажите свои настоящие знания! 🚀
    """

    await query.edit_message_text(middle_text)
    await show_question_from_menu(query, context)


async def show_question_from_menu(query, context):
    """
    Показывает первый вопрос ВСЕГДА новым сообщением
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

    # Добавляем подсказку для Middle режима
    level = context.user_data.get('level')
    if level == 'middle':
        question_text += "\n\n⚡ Всего 1 попытка!"

    # ВСЕГДА отправляем НОВОЕ сообщение с вопросом
    message = await query.message.reply_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index)
    )
    context.user_data['last_question_message_id'] = message.message_id


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

    # РЕДАКТИРУЕМ текущее сообщение вместо отправки нового
    await query.edit_message_text(cancel_text, reply_markup=None)

    # Ждем немного и показываем главное меню
    await asyncio.sleep(1.5)
    await main_menu(query, context)


async def main_menu(query, context):
    """
    Возвращает в главное меню из любого места С ПОЛНОЙ ОЧИСТКОЙ ЧАТА
    """
    from core.services.stats import StatsService
    from utils.keyboards import create_main_menu_keyboard

    user = query.from_user

    # Инициализируем пользователя
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

    # ПОЛНАЯ ОЧИСТКА ВСЕХ СООБЩЕНИЙ БОТА
    try:
        chat_id = query.message.chat_id
        current_message_id = query.message.message_id

        print(f"🔍 Полная очистка чата: текущее сообщение ID: {current_message_id}")

        # Удаляем ВСЕ предыдущие сообщения бота (увеличиваем диапазон)
        deleted_count = 0
        for i in range(1, 51):  # увеличиваем до 50 сообщений
            try:
                await context.bot.delete_message(chat_id, current_message_id - i)
                deleted_count += 1
                print(f"🔍 Удалили сообщение ID: {current_message_id - i}")
            except Exception as e:
                # Пропускаем ошибки "сообщение не найдено"
                if "message to delete not found" not in str(e) and "message can't be deleted" not in str(e):
                    print(f"⚠️ Ошибка удаления {current_message_id - i}: {e}")

        print(f"✅ Удалено сообщений: {deleted_count}")

    except Exception as e:
        print(f"⚠️ Не удалось очистить чат: {e}")

    # РЕДАКТИРУЕМ текущее сообщение (оно осталось после очистки)
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

Весь прогресс сброшен.
Удачи! 🍀
    """

    # Редактируем сообщение с результатом
    await query.edit_message_text(restart_text, reply_markup=None)

    # Ждем немного перед началом нового теста
    await asyncio.sleep(1.5)

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
    from utils.keyboards import create_stats_keyboard

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

    # ЗАМЕНИТЬ: await main_menu(query, context) на:
    await query.edit_message_text(
        stats_text,
        reply_markup=create_stats_keyboard()
    )


async def process_answer(query, data, context):
    """
    Обрабатывает ответ пользователя - результат выше, вопрос всегда последний
    """
    parts = data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])

    questions = context.user_data['questions']
    question = questions[question_index]
    level = context.user_data.get('level', 'junior')

    # Проверяем правильность ответа
    is_correct = answer_index == question['correct_answer']

    if is_correct:
        context.user_data['score'] += 1
        result_icon = "✅"
        result_text = "Правильно!"
    else:
        result_icon = "❌"
        correct_answer_number = question['correct_answer'] + 1
        result_text = f"Неправильно. Правильный ответ: {correct_answer_number}"

        # ДЛЯ MIDDLE: неправильный ответ = конец теста
        if level == 'middle':
            await finish_middle_test_early(query, context, question_index + 1)
            return

    result_message = f"""{result_icon} Вопрос {question_index + 1}: {result_text}

💡 {question['explanation']}"""

    # 1. Сначала отправляем результат ответа
    await query.message.reply_text(result_message)

    # Переходим к следующему вопросу
    context.user_data['current_question'] += 1

    if QuizService.is_quiz_finished(context):
        await finish_test_from_callback(query, context)
        return

    # 2. Ждем немного и показываем СЛЕДУЮЩИЙ вопрос (новое сообщение)
    await asyncio.sleep(1)
    await show_next_question_always_new(query, context)


async def show_next_question_always_new(query, context):
    """
    Показывает следующий вопрос ВСЕГДА новым сообщением
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

    # Добавляем подсказку для Middle режима
    level = context.user_data.get('level')
    if level == 'middle':
        question_text += "\n\n⚡ Всего 1 попытка!"

    # ВСЕГДА отправляем НОВОЕ сообщение с вопросом
    message = await query.message.reply_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index)
    )
    context.user_data['last_question_message_id'] = message.message_id


async def finish_test_from_callback(query, context):
    """
    Завершает тест при вызове из callback
    """
    from utils.keyboards import create_restart_keyboard

    score, total = QuizService.get_quiz_results(context)
    level = context.user_data.get('level', 'junior')

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

    # СОХРАНЯЕМ РЕЗУЛЬТАТ ТЕСТА С УЧЕТОМ УРОВНЯ
    StatsService.save_test_result(
        user_id=query.from_user.id,
        score=score,
        total_questions=total,
        level=level
    )

    # Очищаем временные данные теста
    for key in ['current_question', 'score', 'last_question_message_id', 'questions']:
        if key in context.user_data:
            del context.user_data[key]

    # Отправляем результат с кнопками
    await query.message.reply_text(
        result_text,
        reply_markup=create_restart_keyboard(),
        parse_mode='Markdown'
    )

async def finish_middle_test_early(query, context, questions_answered):
    """
    Завершает тест Middle при неправильном ответе
    """
    from utils.keyboards import create_restart_keyboard

    score = context.user_data['score']
    level = context.user_data.get('level', 'middle')

    result_text = f"""
💥 Тест завершен!

В режиме Middle всего одна попытка на вопрос.

📊 Ваш результат:
• Правильных ответов: {score}/{questions_answered}
• Вопросов пройдено: {questions_answered}

💡 Попробуйте режим Junior для обучения!
    """

    # СОХРАНЯЕМ РЕЗУЛЬТАТ ТЕСТА С УЧЕТОМ УРОВНЯ
    StatsService.save_test_result(
        user_id=query.from_user.id,
        score=score,
        total_questions=questions_answered,
        level=level
    )

    # Очищаем данные
    for key in ['current_question', 'score', 'questions']:
        if key in context.user_data:
            del context.user_data[key]

    await query.message.reply_text(
        result_text,
        reply_markup=create_restart_keyboard(),
        parse_mode='Markdown'
    )


async def confirm_reset_stats(query, context):
    """
    Показывает подтверждение сброса статистики
    """
    from utils.keyboards import create_confirmation_keyboard

    warning_text = """
⚠️ Внимание! Вы собираетесь сбросить всю статистику**

Это действие:
• Удалит всю историю тестов
• Сбросит все достижения  
• Нельзя будет отменить!

Вы уверены что хотите продолжить?
    """

    await query.edit_message_text(
        warning_text,
        reply_markup=create_confirmation_keyboard()
    )


async def reset_stats(query, context):
    """
    Сбрасывает статистику пользователя и возвращает в главное меню
    """
    from data.storage import storage
    import asyncio

    user_id = query.from_user.id

    # Сбрасываем статистику
    storage.reset_user_stats(user_id)

    # Показываем сообщение об успехе
    success_text = """
🗑️ Статистика сброшена!

Вся ваша история тестов и достижения удалены.

Начните с чистого листа! 🚀
    """

    await query.edit_message_text(success_text, reply_markup=None)

    # Ждем 2 секунды и показываем главное меню
    await asyncio.sleep(2)
    await main_menu(query, context)
