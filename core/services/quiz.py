from data.database import load_questions


class QuizService:
    def __init__(self):
        self.questions = load_questions()

    async def start_quiz(self, context):
        """Начинает новый тест"""
        if not self.questions:
            return False

        context.user_data['questions'] = self.questions
        context.user_data['current_question'] = 0
        context.user_data['score'] = 0
        return True

    @staticmethod
    async def get_current_question(context):
        """Возвращает текущий вопрос"""
        current_index = context.user_data.get('current_question', 0)
        questions = context.user_data.get('questions', [])

        if current_index >= len(questions):
            return None

        return questions[current_index], current_index

    @staticmethod
    async def process_answer(context, question_index, answer_index):
        """Обрабатывает ответ пользователя"""
        questions = context.user_data['questions']
        question = questions[question_index]

        # Проверяем правильность ответа
        is_correct = answer_index == question['correct_answer']

        if is_correct:
            context.user_data['score'] += 1
            result_icon = "✅"
            result_text = "Правильно!"
        else:
            result_icon = "❌"
            result_text = f"Не правильно!"

        # Формируем сообщение с результатом
        result_message = f"""{result_icon} Вопрос {question_index + 1}: {result_text}

💡 {question['explanation']}"""

        # Переходим к следующему вопросу
        context.user_data['current_question'] = question_index + 1

        return result_message, is_correct

    @staticmethod
    def is_quiz_finished(context):
        """Проверяет завершен ли тест (статический)"""
        current_index = context.user_data.get('current_question', 0)
        questions = context.user_data.get('questions', [])
        return current_index >= len(questions)

    @staticmethod
    def get_quiz_results(context):
        """Возвращает результаты теста (статический)"""
        score = context.user_data.get('score', 0)
        total = len(context.user_data.get('questions', []))
        return score, total
