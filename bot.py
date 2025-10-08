from core.application import create_application


def main():
    """
    Основная функция запуска бота
    """
    print("🚀 Запускаю QA Testing Bot...")

    # Создаем приложение бота
    application = create_application()

    print("✅ Бот запущен и готов к работе!")
    print("⏹️  Для остановки нажмите Ctrl+C")

    # Запускаем бота в режиме опроса (polling)
    application.run_polling()


if __name__ == "__main__":
    main()
