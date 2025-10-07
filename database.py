import json


def load_questions():
    try:
        with open('questions.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('questions', [])
    except FileNotFoundError:
        print("❌ Файл questions.json не найден!")
        return []
    except json.JSONDecodeError:
        print("❌ Ошибка в формате JSON файла!")
        return []

