from data.database import load_questions


class QuizService:
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
