import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler


def setup_environment():
    """Настраивает окружение для разработки и продакшена"""
    # Проверяем есть ли .env файл
    if not os.path.exists('.env'):
        return

    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded for development")
    except ImportError:
        print("⚠️ python-dotenv not installed, but .env file exists")


# Вызываем настройку окружения
setup_environment()


from core.handlers.commands import start_command, restart_command, cancel_command
from core.handlers.callbacks import handle_button_click


def create_application():
    """
    Создает и настраивает приложение бота
    """
    # Получаем токен из переменных окружения
    BOT_TOKEN = os.environ.get('BOT_TOKEN')

    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN not found in environment variables. "
                         "Please set BOT_TOKEN in Railway variables.")

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Регистрируем обработчик нажатий на inline-кнопки
    application.add_handler(CallbackQueryHandler(handle_button_click))

    return application
