import random
from data.database import load_questions


class QuizService:
    @staticmethod
    def shuffle_questions(questions):
        """Перемешивает вопросы в случайном порядке"""
        shuffled = questions.copy()
        random.shuffle(shuffled)
        return shuffled

    @staticmethod
    def shuffle_options(question):
        """Перемешивает варианты ответов и возвращает новый correct_answer индекс"""
        options = question['options'].copy()
        correct_answer = question['correct_answer']

        # Сохраняем правильный ответ до перемешивания
        correct_option = options[correct_answer]

        # Перемешиваем варианты
        random.shuffle(options)

        # Находим новый индекс правильного ответа
        new_correct_answer = options.index(correct_option)

        return options, new_correct_answer

    @staticmethod
    async def get_current_question(context):
        """Возвращает текущий вопрос"""
        current_index = context.user_data.get('current_question', 0)
        questions = context.user_data.get('questions', [])

        if current_index >= len(questions):
            return None

        return questions[current_index], current_index

    @staticmethod
    def is_quiz_finished(context):
        """Проверяет завершен ли тест"""
        current_index = context.user_data.get('current_question', 0)
        questions = context.user_data.get('questions', [])
        return current_index >= len(questions)

    @staticmethod
    def get_quiz_results(context):
        """Возвращает результаты теста"""
        score = context.user_data.get('score', 0)
        total = len(context.user_data.get('questions', []))
        return score, total
