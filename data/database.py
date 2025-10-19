import json
from typing import List, Dict, Any
from .models import Question


def load_questions() -> List[Dict[str, Any]]:
    """
    Загружает вопросы из JSON файла
    """
    try:
        with open('data/questions.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('questions', [])
    except FileNotFoundError:
        print("❌ Файл data/questions.json не найден!")
        return []


def load_questions_as_models() -> List[Question]:
    """
    Загружает вопросы как объекты моделей
    """
    questions_data = load_questions()
    questions = []

    for q_data in questions_data:
        question = Question(
            id=q_data['id'],
            question=q_data['question'],
            options=q_data['options'],
            correct_answer=q_data['correct_answer'],
            explanation=q_data.get('explanation', ''),
            topic=q_data.get('topic', 'general'),
            difficulty=q_data.get('difficulty', 'easy')
        )
        questions.append(question)

    return questions


def get_questions_by_topic(topic: str) -> List[Question]:
    """
    Возвращает вопросы по теме
    """
    all_questions = load_questions_as_models()
    return [q for q in all_questions if q.topic == topic]


def get_questions_by_difficulty(difficulty: str) -> List[Question]:
    """
    Возвращает вопросы по сложности
    """
    all_questions = load_questions_as_models()
    return [q for q in all_questions if q.difficulty == difficulty]
