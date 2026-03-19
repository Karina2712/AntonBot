import logging
from telebot import TeleBot
from src.config.settings import settings  # ← АБСОЛЮТНЫЙ!
from src.handlers.client import register_client_handlers
from src.handlers.admin import register_admin_handlers  
from src.handlers.callback import register_callback_handlers
from src.core.scheduler import Scheduler

logging.getLogger('telebot').setLevel(logging.CRITICAL)

def create_bot():
    bot = TeleBot(settings.TOKEN)
    register_client_handlers(bot)
    register_admin_handlers(bot)
    register_callback_handlers(bot)
    return bot

def run_bot():
    bot = create_bot()
    scheduler = Scheduler(bot, settings)
    scheduler.start()
    bot.infinity_polling()
