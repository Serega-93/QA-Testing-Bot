import sqlite3
import os
from typing import List, Optional
from datetime import datetime
from .models import User, UserStats, Achievement


class Storage:
    def __init__(self, db_path: str = "data/qa_bot.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Инициализирует базу данных и таблицы"""
        print(f"📁 Создаем папку для: {os.path.dirname(self.db_path)}")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        print(f"🔧 Подключаемся к БД: {self.db_path}")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Создаем таблицу пользователей ПЕРВОЙ
            print("🛠️ Создаем таблицу users...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT
                )
            ''')

            # Создаем таблицу статистики
            print("🛠️ Создаем таблицу user_stats...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_tests INTEGER DEFAULT 0,
                    best_score INTEGER DEFAULT 0,
                    total_correct_answers INTEGER DEFAULT 0,
                    total_questions_answered INTEGER DEFAULT 0,
                    last_test_date TEXT,
                    junior_tests INTEGER DEFAULT 0,
                    junior_best_score INTEGER DEFAULT 0,
                    middle_tests INTEGER DEFAULT 0,
                    middle_best_score INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Создаем таблицу результатов тестов
            print("🛠️ Создаем таблицу test_results...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    score INTEGER,
                    total_questions INTEGER,
                    test_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Создаем таблицу достижений
            print("🛠️ Создаем таблицу achievements...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    achievement_name TEXT,
                    earned_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')

            # Проверяем что таблицы создались
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ Созданные таблицы: {tables}")
            self._update_database_schema()

            conn.commit()

        print("✅ БД инициализирована!")


    def save_user(self, user: User):
        """Сохраняет или обновляет пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user.user_id, user.username, user.first_name, user.created_at))
            conn.commit()

    def save_test_result(self, user_id: int, score: int, total_questions: int):
        """Сохраняет результат теста и обновляет статистику"""
        test_date = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Сохраняем результат теста
            cursor.execute('''
                INSERT INTO test_results (user_id, score, total_questions, test_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, score, total_questions, test_date))

            # Обновляем статистику пользователя
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats 
                (user_id, total_tests, best_score, total_correct_answers, total_questions_answered, last_test_date)
                VALUES (
                    ?,
                    COALESCE((SELECT total_tests FROM user_stats WHERE user_id = ?), 0) + 1,
                    MAX(COALESCE((SELECT best_score FROM user_stats WHERE user_id = ?), 0), ?),
                    COALESCE((SELECT total_correct_answers FROM user_stats WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT total_questions_answered FROM user_stats WHERE user_id = ?), 0) + ?,
                    ?
                )
            ''', (user_id, user_id, user_id, score, user_id, score, user_id, total_questions, test_date))

            conn.commit()

    def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Возвращает статистику пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_stats WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            if row:
                return UserStats(
                    user_id=row[0],
                    total_tests=row[1],
                    best_score=row[2],
                    total_correct_answers=row[3],
                    total_questions_answered=row[4],
                    last_test_date=row[5]
                )
            return None

    def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """Возвращает достижения пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, achievement_name, earned_date 
                FROM achievements WHERE user_id = ?
            ''', (user_id,))

            return [Achievement(row[0], row[1], row[2]) for row in cursor.fetchall()]


    def debug_print_all_data(self):
        """Выводит все данные для отладки"""
        print("🔍 ДЕБАГ: Проверяем данные в БД:")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Проверяем пользователей
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"👤 Пользователи: {users}")

            # Проверяем статистику
            cursor.execute("SELECT * FROM user_stats")
            stats = cursor.fetchall()
            print(f"📊 Статистика: {stats}")

            # Проверяем результаты тестов
            cursor.execute("SELECT * FROM test_results")
            results = cursor.fetchall()
            print(f"🎯 Результаты тестов: {results}")


    def reset_user_stats(self, user_id: int):
        """
        Полностью сбрасывает статистику пользователя
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Удаляем статистику
            cursor.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))

            # Удаляем результаты тестов
            cursor.execute('DELETE FROM test_results WHERE user_id = ?', (user_id,))

            # Удаляем достижения
            cursor.execute('DELETE FROM achievements WHERE user_id = ?', (user_id,))

            conn.commit()

        print(f"🗑️ Статистика пользователя {user_id} сброшена")

    def save_test_result_with_level(self, user_id: int, score: int, total_questions: int, level: str):
        """Сохраняет результат теста с учетом уровня сложности"""
        test_date = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Сохраняем результат теста
            cursor.execute('''
                INSERT INTO test_results (user_id, score, total_questions, test_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, score, total_questions, test_date))

            # Обновляем статистику в зависимости от уровня
            if level == "junior":
                cursor.execute('''
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, total_tests, best_score, total_correct_answers, total_questions_answered, 
                     last_test_date, junior_tests, junior_best_score, junior_total_correct, junior_total_questions)
                    VALUES (
                        ?,
                        COALESCE((SELECT total_tests FROM user_stats WHERE user_id = ?), 0) + 1,
                        MAX(COALESCE((SELECT best_score FROM user_stats WHERE user_id = ?), 0), ?),
                        COALESCE((SELECT total_correct_answers FROM user_stats WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT total_questions_answered FROM user_stats WHERE user_id = ?), 0) + ?,
                        ?,
                        COALESCE((SELECT junior_tests FROM user_stats WHERE user_id = ?), 0) + 1,
                        MAX(COALESCE((SELECT junior_best_score FROM user_stats WHERE user_id = ?), 0), ?),
                        COALESCE((SELECT junior_total_correct FROM user_stats WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT junior_total_questions FROM user_stats WHERE user_id = ?), 0) + ?
                    )
                ''', (user_id, user_id, user_id, score, user_id, score, user_id, total_questions,
                      test_date, user_id, user_id, score, user_id, score, user_id, total_questions))

            elif level == "middle":
                cursor.execute('''
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, total_tests, best_score, total_correct_answers, total_questions_answered, 
                     last_test_date, middle_tests, middle_best_score, middle_total_correct, middle_total_questions)
                    VALUES (
                        ?,
                        COALESCE((SELECT total_tests FROM user_stats WHERE user_id = ?), 0) + 1,
                        MAX(COALESCE((SELECT best_score FROM user_stats WHERE user_id = ?), 0), ?),
                        COALESCE((SELECT total_correct_answers FROM user_stats WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT total_questions_answered FROM user_stats WHERE user_id = ?), 0) + ?,
                        ?,
                        COALESCE((SELECT middle_tests FROM user_stats WHERE user_id = ?), 0) + 1,
                        MAX(COALESCE((SELECT middle_best_score FROM user_stats WHERE user_id = ?), 0), ?),
                        COALESCE((SELECT middle_total_correct FROM user_stats WHERE user_id = ?), 0) + ?,
                        COALESCE((SELECT middle_total_questions FROM user_stats WHERE user_id = ?), 0) + ?
                    )
                ''', (user_id, user_id, user_id, score, user_id, score, user_id, total_questions,
                      test_date, user_id, user_id, score, user_id, score, user_id, total_questions))

            conn.commit()

    def _update_database_schema(self):
        """Обновляет схему базы данных добавляя недостающие колонки"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Добавляем недостающие колонки если их нет
            columns_to_add = [
                'junior_total_correct INTEGER DEFAULT 0',
                'junior_total_questions INTEGER DEFAULT 0',
                'middle_total_correct INTEGER DEFAULT 0',
                'middle_total_questions INTEGER DEFAULT 0'
            ]

            for column_def in columns_to_add:
                column_name = column_def.split(' ')[0]
                try:
                    cursor.execute(f'ALTER TABLE user_stats ADD COLUMN {column_def}')
                    print(f"✅ Добавлена колонка {column_name}")
                except sqlite3.OperationalError:
                    # Колонка уже существует - это нормально
                    pass


# Глобальный экземпляр хранилища
storage = Storage()
