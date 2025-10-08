from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Question:
    """Модель вопроса"""
    id: int
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    topic: str = "general"
    difficulty: str = "easy"


@dataclass
class QuizResult:
    """Модель результата теста"""
    user_id: int
    score: int
    total_questions: int
    correct_answers: int
    percentage: float


class UserStats:
    """Модель статистики пользователя"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.quizzes_taken = 0
        self.best_score = 0
        self.average_score = 0.0
