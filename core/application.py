from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN

from core.handlers.commands import start_command, restart_command, cancel_command
from core.handlers.callbacks import handle_button_click


def create_application():
    """
    Создает и настраивает приложение бота
    """
    # Исправленная инициализация для новой версии библиотеки
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("restart", restart_command))
    application.add_handler(CommandHandler("cancel", cancel_command))

    # Регистрируем обработчик нажатий на inline-кнопки
    application.add_handler(CallbackQueryHandler(handle_button_click))

    return application
