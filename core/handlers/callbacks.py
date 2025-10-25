from telegram import Update
from telegram.ext import ContextTypes
import asyncio
from utils.feedback import get_feedback
from utils.keyboards import create_quiz_keyboard
from core.services.quiz import QuizService
from core.services.stats import StatsService
from data.database import load_questions
from data.storage import storage


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

🎓 Junior:
• Неограниченные попытки
• Подходит для начинающих

💪 Middle:
• 1 попытка на ответ
• Ошибка = конец теста

Выберите уровень:
    """

    await query.edit_message_text(
        level_selection_text,
        reply_markup=create_level_selection_keyboard()
    )


async def start_junior_quiz(query, context):
    """
    Начинает тест в режиме Junior
    """
    questions = load_questions()
    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    # ПЕРЕМЕШИВАЕМ вопросы в случайном порядке
    shuffled_questions = QuizService.shuffle_questions(questions)

    context.user_data.update({
        'questions': shuffled_questions,
        'current_question': 0,
        'score': 0,
        'level': 'junior'
    })

    junior_text = """
🎓 Режим: Junior

Учитесь в своем темпе! Ошибаться - это нормально! 📚

Удачи! 🍀
    """

    await query.edit_message_text(junior_text, reply_markup=None)
    storage.track_message(query.from_user.id, query.message.message_id)

    await asyncio.sleep(1.5)
    await show_question_from_menu(query, context)


async def start_middle_quiz(query, context):
    """
    Начинает тест в режиме Middle
    """
    questions = load_questions()
    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    # ПЕРЕМЕШИВАЕМ вопросы в случайном порядке
    shuffled_questions = QuizService.shuffle_questions(questions)

    context.user_data.update({
        'questions': shuffled_questions,
        'current_question': 0,
        'score': 0,
        'level': 'middle'
    })

    middle_text = """
💪 Режим: Middle

Всего 1 попытка на ответ! Ошибка = конец теста! ⚡

Покажите свои настоящие знания! 🚀
    """

    await query.edit_message_text(middle_text, reply_markup=None)
    storage.track_message(query.from_user.id, query.message.message_id)

    await asyncio.sleep(1.5)
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

    # ПЕРЕМЕШИВАЕМ варианты ответов
    shuffled_options, new_correct_index = QuizService.shuffle_options(question)

    # Сохраняем новый индекс правильного ответа в контексте
    context.user_data[f'correct_index_{current_index}'] = new_correct_index

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(context.user_data['questions'])}
{question['question']}

""" + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(shuffled_options)])

    level = context.user_data.get('level')
    if level == 'middle':
        question_text += "\n\n⚡ Всего 1 попытка!"

    # ВСЕГДА отправляем НОВОЕ сообщение с вопросом
    message = await query.message.reply_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index, shuffled_options)
    )

    storage.track_message(query.from_user.id, message.message_id)
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
    Возвращает в главное меню с БЫСТРОЙ очисткой
    """
    from utils.keyboards import create_main_menu_keyboard

    user = query.from_user
    user_id = user.id

    # Инициализируем пользователя
    StatsService.init_user(user_id, user.username, user.first_name)

    # Получаем статистику
    stats = StatsService.get_user_stats(user_id)

    # Формируем блоки статистики для каждого уровня
    junior_stats = ""
    middle_stats = ""

    if stats and (stats.junior_tests > 0 or stats.middle_tests > 0):
        if stats.junior_tests > 0:
            junior_success = StatsService.calculate_level_success_rate(stats, "junior")
            junior_best_percentage = StatsService.calculate_best_score_percentage(stats, "junior")
            junior_stats = f"""🎓 Junior
    • Тестов: {stats.junior_tests}
    • Последний результат: {stats.junior_total_correct}/{stats.junior_total_questions}
    • Успешность: {junior_success}%
    • Лучший результат: {stats.junior_best_score}/100 ({junior_best_percentage}%)"""

        if stats.middle_tests > 0:
            middle_success = StatsService.calculate_level_success_rate(stats, "middle")
            middle_best_percentage = StatsService.calculate_best_score_percentage(stats, "middle")
            middle_stats = f"""💪 Middle
    • Тестов: {stats.middle_tests}
    • Последний результат: {stats.middle_total_correct}/{stats.middle_total_questions}
    • Успешность: {middle_success}%
    • Лучший результат: {stats.middle_best_score}/100 ({middle_best_percentage}%)"""

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
    • Объяснения к каждому ответу  
    • Статистика ваших результатов

Готовы начать? 🚀"""

    # 1. ОЧИСТКА СООБЩЕНИЙ через общую функцию
    await clear_chat_history(query, context)

    # 2. РЕДАКТИРУЕМ текущее сообщение
    await query.edit_message_text(
        welcome_text,
        reply_markup=create_main_menu_keyboard()
    )


async def restart_from_button(query, context):
    """
    Перезапускает тест при нажатии на кнопку
    """

    await clear_chat_history(query, context)

    # ЗАГРУЖАЕМ ВОПРОСЫ ЗАНОВО
    questions = load_questions()
    if not questions:
        await query.edit_message_text("❌ Вопросы не найдены!")
        return

    # Очищаем данные теста
    for key in ['current_question', 'score', 'last_question_message_id', 'questions']:
        if key in context.user_data:
            del context.user_data[key]

    # ЗАГРУЖАЕМ НОВЫЕ ВОПРОСЫ
    context.user_data['questions'] = QuizService.shuffle_questions(questions)
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    restart_text = """
🔄 Тест начат заново!
Весь прогресс сброшен.
Удачи! 🍀
    """

    await query.edit_message_text(restart_text, reply_markup=None)
    await asyncio.sleep(1.5)

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

    await query.edit_message_text(
        stats_text,
        reply_markup=create_stats_keyboard()
    )


async def process_answer(query, callback_data, context):
    """
    Обрабатывает ответ пользователя
    """
    parts = callback_data.split('_')
    question_index = int(parts[1])
    answer_index = int(parts[2])

    questions = context.user_data['questions']
    question = questions[question_index]
    level = context.user_data.get('level', 'junior')

    # Получаем ПРАВИЛЬНЫЙ индекс из контекста
    correct_index = context.user_data.get(f'correct_index_{question_index}', question['correct_answer'])

    # Проверяем правильность ответа
    is_correct = answer_index == correct_index

    if is_correct:
        context.user_data['score'] += 1
        result_icon = "✅"
        result_text = "Правильно!"
    else:
        result_icon = "❌"
        correct_answer_number = correct_index + 1
        result_text = f"Неправильно!"

        # ДЛЯ MIDDLE: неправильный ответ = конец теста
        if level == 'middle':
            await finish_middle_test_early(query, context, question_index + 1)
            return

    result_message = f"""{result_icon} Вопрос {question_index + 1}: {result_text}

💡 {question['explanation']}"""

    # 1. Сначала отправляем результат ответа
    result_msg = await query.message.reply_text(result_message)

    # СОХРАНЯЕМ ID сообщения с результатом
    storage.track_message(query.from_user.id, result_msg.message_id)

    # Переходим к следующему вопросу
    context.user_data['current_question'] += 1

    if QuizService.is_quiz_finished(context):
        await finish_test_from_callback(query, context)
        return

    # 2. Ждем немного и показываем СЛЕДУЮЩИЙ вопрос
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

    # ПЕРЕМЕШИВАЕМ варианты ответов
    shuffled_options, new_correct_index = QuizService.shuffle_options(question)

    # Сохраняем новый индекс правильного ответа в контексте
    context.user_data[f'correct_index_{current_index}'] = new_correct_index

    question_text = f"""
🎯 Вопрос {current_index + 1}/{len(context.user_data['questions'])}
{question['question']}

""" + "\n".join([f"{i + 1}. {option}" for i, option in enumerate(shuffled_options)])

    level = context.user_data.get('level')
    if level == 'middle':
        question_text += "\n\n⚡ Всего 1 попытка!"

    # ВСЕГДА отправляем НОВОЕ сообщение с вопросом
    message = await query.message.reply_text(
        question_text,
        reply_markup=create_quiz_keyboard(question, current_index, shuffled_options)
    )

    storage.track_message(query.from_user.id, message.message_id)
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
    result_message = await query.message.reply_text(
        result_text,
        reply_markup=create_restart_keyboard(),
        parse_mode='Markdown'
    )

    # СОХРАНЯЕМ ID сообщения с результатом теста
    storage.track_message(query.from_user.id, result_message.message_id)


async def finish_middle_test_early(query, context, questions_answered):
    """
    Завершает тест Middle при неправильном ответе и возвращает в главное меню
    """
    from utils.keyboards import create_restart_keyboard
    from core.services.stats import StatsService

    score = context.user_data['score']
    level = context.user_data.get('level', 'middle')
    total_questions = len(context.user_data.get('questions', []))

    result_text = f"""
💥 Тест завершен!

В режиме Middle всего одна попытка на ответ.

📊 Ваш результат:
• Правильных ответов: {score}/{questions_answered}
• Вопросов пройдено: {questions_answered}
• Всего вопросов в тесте: {total_questions}

💡 Попробуйте режим Junior для обучения!
    """

    # СОХРАНЯЕМ РЕЗУЛЬТАТ ТЕСТА С УЧЕТОМ УРОВНЯ - ВАЖНО: сохраняем общее количество вопросов
    StatsService.save_test_result(
        user_id=query.from_user.id,
        score=score,
        total_questions=total_questions,
        level=level
    )

    # Сохраняем для отображения в статистике
    context.user_data['last_score'] = score
    context.user_data['last_total'] = total_questions

    # Очищаем данные теста, но оставляем статистику для отображения
    for key in ['current_question', 'score', 'questions', 'last_question_message_id']:
        if key in context.user_data:
            del context.user_data[key]

    # Отправляем результат с кнопками для продолжения
    result_message = await query.message.reply_text(
        result_text,
        reply_markup=create_restart_keyboard(),
        parse_mode='Markdown'
    )

    # СОХРАНЯЕМ ID сообщения с результатом теста
    storage.track_message(query.from_user.id, result_message.message_id)


async def confirm_reset_stats(query, context):
    """
    Показывает подтверждение сброса статистики
    """
    from utils.keyboards import create_confirmation_keyboard

    warning_text = """
⚠️ Внимание! Вы собираетесь сбросить всю статистику!

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


async def clear_chat_history(query, context):
    """
    Очищает историю сообщений бота
    """
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    current_message_id = query.message.message_id

    try:
        # 1. ОТПРАВЛЯЕМ АНИМИРОВАННОЕ УВЕДОМЛЕНИЕ
        cleanup_msg = await query.message.reply_text("🧹 Очистка истории...")
        storage.track_message(user_id, cleanup_msg.message_id)

        # 2. АНИМАЦИЯ ЗАГРУЗКИ
        dots = ["", ".", "..", "..."]
        for i in range(8):  # 2 секунды анимации
            await cleanup_msg.edit_text(f"🧹 Очистка истории{dots[i % 4]}")
            await asyncio.sleep(0.25)

        # 3. ОСНОВНАЯ ЛОГИКА ОЧИСТКИ (как в варианте 1)
        message_ids = storage.get_user_messages(user_id)
        batch_size = 10
        deleted_count = 0

        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            messages_to_delete = [msg_id for msg_id in batch if msg_id != current_message_id]

            if messages_to_delete:
                delete_tasks = []
                for message_id in messages_to_delete:
                    try:
                        task = context.bot.delete_message(chat_id, message_id)
                        delete_tasks.append(task)
                    except Exception:
                        pass

                if delete_tasks:
                    await asyncio.gather(*delete_tasks, return_exceptions=True)
                    deleted_count += len(messages_to_delete)

                await asyncio.sleep(0.1)

        # 4. ФИНАЛЬНОЕ УВЕДОМЛЕНИЕ
        await cleanup_msg.edit_text(f"✅ История очищена ({deleted_count} сообщений)")

        # 5. УДАЛЯЕМ УВЕДОМЛЕНИЕ ЧЕРЕЗ 1.5 СЕКУНДЫ
        await asyncio.sleep(1.5)
        await context.bot.delete_message(chat_id, cleanup_msg.message_id)

        # 6. Очищаем список сообщений
        storage.clear_user_messages(user_id)
        storage.track_message(user_id, current_message_id)

    except Exception as e:
        print(f"⚠️ Ошибка при очистке сообщений: {e}")
