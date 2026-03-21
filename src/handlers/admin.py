import telebot
from datetime import datetime, timedelta
import re
import threading
import time
import json
import os
import logging
from peewee import SqliteDatabase
from contextlib import contextmanager

from config.settings import settings
from utils.keyboards import back_keyboard
from utils.states import user_states
from src.database.models import Booking
from services.stats import get_stats

logger = logging.getLogger(__name__)
db = SqliteDatabase('bookings.db')

_admin_handlers_registered = False

@contextmanager
def db_connection():
    try:
        db.connect()
        db.create_tables([Booking], safe=True)
        yield db
    finally:
        db.close()

def safe_parse_datetime(dt_str):
    try:
        return datetime.fromisoformat(dt_str)
    except:
        return None

def get_custom_reminders():
    try:
        if os.path.exists('reminders.json'):
            with open('reminders.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {
        'day_before': '👋 Напоминаю! Завтра в {time} у Антона запись на татуировку 💉\n\n📲 Подтвердите или отмените: /yes или /no',
        'two_hours': '⏰ Через 2 часа ваша запись у Антона! 💉\n\n⏰ {time}\n\nНе опаздывайте! 🚀',
        'evening': '🌙 Напоминание на завтра!\n\n💉 Запись: {time}\n👨‍🎨 Мастер: Антон\n\nДо встречи! ✨'
    }

def save_custom_reminders(templates):
    try:
        with open('reminders.json', 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        logger.info("✅ Шаблоны напоминаний сохранены")
    except Exception as e:
        logger.error(f"Ошибка сохранения reminders: {e}")

def extract_chat_id(text):
    patterns = [
        r'chat_id[:\s]*(-?\d+)',
        r'id[:\s]*(-?\d+)',
        r'(-?\d{5,})'
    ]
    text_clean = re.sub(r'\\', '', text)  # убираем экранирование
    for pattern in patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def check_existing_reminders(bot):
    try:
        with db_connection():
            bookings = Booking.select().where(Booking.datetime > datetime.now())
            for booking in bookings:
                schedule_exact_reminders(bot, booking.chat_id, booking.datetime)
    except Exception as e:
        logger.error(f"Ошибка проверки напоминаний: {e}")

def schedule_exact_reminders(bot, chat_id, booking_dt):
    def send_day_reminder():
        templates = get_custom_reminders()
        time_str = booking_dt.strftime('%d.%m.%Y %H:%M')
        text = templates['day_before'].format(time=time_str)
        try:
            bot.send_message(chat_id, text)
        except:
            pass

    def send_two_hours():
        templates = get_custom_reminders()
        time_str = booking_dt.strftime('%H:%M')
        text = templates['two_hours'].format(time=time_str)
        try:
            bot.send_message(chat_id, text)
        except:
            pass

    def send_evening():
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
        time_str = booking_dt.strftime('%H:%M')
        templates = get_custom_reminders()
        text = templates['evening'].format(time=time_str)
        try:
            bot.send_message(chat_id, f"{text}\n📅 {tomorrow}")
        except:
            pass

    day_before = booking_dt - timedelta(days=1)
    if day_before > datetime.now():
        threading.Timer((day_before - datetime.now()).total_seconds(), send_day_reminder).start()
    
    two_hours = booking_dt - timedelta(hours=2)
    if two_hours > datetime.now():
        threading.Timer((two_hours - datetime.now()).total_seconds(), send_two_hours).start()
    
    today_19 = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
    if today_19 > datetime.now() and booking_dt.date() == (datetime.now() + timedelta(days=1)).date():
        threading.Timer((today_19 - datetime.now()).total_seconds(), send_evening).start()

def start_reminder_scheduler(bot):
    check_existing_reminders(bot)
    logger.info("✅ Планировщик напоминаний запущен")

def admin_exit_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("❌ Выход из админки")
    return markup

def reminders_editor_menu():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📅 За день", callback_data="edit_day"),
        telebot.types.InlineKeyboardButton("⏰ За 2ч",

