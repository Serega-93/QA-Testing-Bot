from data.storage import storage
from datetime import datetime


class StatsService:
    @staticmethod
    def init_user(user_id: int, username: str, first_name: str):
        """Инициализирует пользователя в системе"""
        from data.models import User
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            created_at=datetime.now().isoformat()
        )
        storage.save_user(user)

    @staticmethod
    def save_test_result(user_id: int, score: int, total_questions: int, level: str = "junior"):
        """Сохраняет результат теста с указанием уровня"""
        storage.save_test_result_with_level(user_id, score, total_questions, level)

    @staticmethod
    def get_user_stats(user_id: int):
        """Возвращает статистику пользователя"""
        return storage.get_user_stats(user_id)

    @staticmethod
    def calculate_level_success_rate(stats, level: str):
        """Рассчитывает процент успешных ответов для конкретного уровня"""
        if not stats:
            return 0

        if level == "junior":
            if stats.junior_total_questions > 0:
                return round((stats.junior_total_correct / stats.junior_total_questions) * 100)
        elif level == "middle":
            # Для Middle считаем успешность последнего теста
            if stats.middle_total_questions > 0:
                return round((stats.middle_total_correct / stats.middle_total_questions) * 100)
        return 0

    @staticmethod
    def calculate_best_score_percentage(stats, level: str):
        """Рассчитывает процент лучшего результата"""
        if not stats:
            return 0

        if level == "junior" and stats.junior_best_score > 0:
            return round((stats.junior_best_score / 100) * 100)
        elif level == "middle" and stats.middle_best_score > 0:
            return round((stats.middle_best_score / 100) * 100)
        return 0
