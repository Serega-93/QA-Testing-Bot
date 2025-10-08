from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


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
class User:
    """Модель пользователя"""
    user_id: int
    username: Optional[str]
    first_name: Optional[str]
    created_at: str


@dataclass
class UserStats:
    """Модель статистики пользователя"""
    user_id: int
    total_tests: int = 0
    best_score: int = 0
    total_correct_answers: int = 0
    total_questions_answered: int = 0
    last_test_date: Optional[str] = None
    junior_tests: int = 0
    junior_best_score: int = 0
    junior_total_correct: int = 0
    junior_total_questions: int = 0
    middle_tests: int = 0
    middle_best_score: int = 0
    middle_total_correct: int = 0
    middle_total_questions: int = 0


@dataclass
class TestResult:
    """Модель результата теста"""
    user_id: int
    score: int
    total_questions: int
    test_date: str


@dataclass
class Achievement:
    """Модель достижения"""
    user_id: int
    achievement_name: str
    earned_date: str
