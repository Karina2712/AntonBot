import logging
from telebot import TeleBot
from src.config.settings import settings
from src.handlers.client import register_client_handlers
from src.handlers.admin import register_admin_handlers  
from src.handlers.callback import register_callback_handlers
from src.core.scheduler import Scheduler

logging.getLogger('telebot').setLevel(logging.CRITICAL)

def create_bot():
    bot = TeleBot(settings.TOKEN)
    
    # 🔥 ПРАВИЛЬНЫЙ ПОРЯДОК С СТРОГОЙ ИЗОЛЯЦИЕЙ
    register_admin_handlers(bot)           # 1. АДМИН - СТРОГО ТОЛЬКО ANTON_CHAT_ID
    register_callback_handlers(bot)        # 2. CALLBACK - ОБЩИЕ ДЛЯ ВСЕХ
    register_client_handlers(bot)          # 3. КЛИЕНТЫ - ВСЕ КРОМЕ ANTON_CHAT_ID
    
    return bot

def run_bot():
    bot = create_bot()
    scheduler = Scheduler(bot, settings)
    scheduler.start()
    bot.infinity_polling()
