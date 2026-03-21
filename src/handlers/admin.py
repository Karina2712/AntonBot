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
    except Exception as e:
        logger.error(f"Ошибка сохранения reminders: {e}")

def extract_chat_id(text):
    match = re.search(r'chat_id:\s*(-?\d+)', text, re.IGNORECASE)
    return match.group(1) if match else None

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
        telebot.types.InlineKeyboardButton("⏰ За 2ч", callback_data="edit_2h"),
        telebot.types.InlineKeyboardButton("🌙 19:00", callback_data="edit_19")
    )
    markup.add(telebot.types.InlineKeyboardButton("❌ Назад", callback_data="admin_back"))
    return markup

# ✅ АДМИНСКИЕ КНОПКИ (ТОЧНО ТАКИЕ ЖЕ)
ADMIN_BUTTONS = {
    "📊 Статистика", "📢 Рассылка акций", "➕ Добавить запись", 
    "👥 Список клиентов", "✏️ Редактировать рассылки", "❌ Выход из админки"
}

def show_admin_panel(bot, chat_id):
    """Показывает админ-панель с кнопками"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    row1 = ["📊 Статистика", "📢 Рассылка акций"]
    row2 = ["➕ Добавить запись", "👥 Список клиентов"]
    row3 = ["✏️ Редактировать рассылки", "❌ Выход из админки"]
    
    for row in [row1, row2, row3]:
        markup.row(*row)
    
    bot.send_message(chat_id, "🔧 **АДМИН ПАНЕЛЬ АКТИВНА**", reply_markup=markup, parse_mode='Markdown')

def register_admin_handlers(bot: telebot.TeleBot):
    global _admin_handlers_registered
    
    if _admin_handlers_registered:
        logger.warning("⚠️ Админ хендлеры уже зарегистрированы")
        return
    
    logger.info("🔧 Регистрация админ хендлеров...")

    # 🔥 #0 КОМАНДА /ADMIN - САМЫЙ ВЫСОКИЙ ПРИОРИТЕТ
    @bot.message_handler(commands=['admin'])
    def admin_command(message):
        if message.chat.id != settings.ANTON_CHAT_ID:
            bot.send_message(message.chat.id, "❌ Доступ запрещен")
            return
        logger.info(f"✅ АДМИН КОМАНДА /admin от {message.chat.id}")
        show_admin_panel(bot, message.chat.id)

    # 🔥 #1 АДМИНСКИЕ КНОПКИ - ОЧЕНЬ ВЫСОКИЙ ПРИОРИТЕТ
    @bot.message_handler(func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text in ADMIN_BUTTONS)
    def handle_admin_buttons(message):
        chat_id = message.chat.id
        text = message.text
        
        logger.info(f"✅ АДМИН КНОПКА НАЖАТА: '{text}' от chat_id={chat_id}")
        
        if text == "❌ Выход из админки":
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "✅ Админ режим отключен", reply_markup=back_keyboard())
            return
        
        elif text == "📊 Статистика":
            try:
                stats_text = get_stats()
                bot.send_message(chat_id, stats_text, parse_mode='Markdown', reply_markup=admin_exit_keyboard())
            except Exception as e:
                logger.error(f"Ошибка статистики: {e}")
                bot.send_message(chat_id, "❌ Ошибка статистики", reply_markup=admin_exit_keyboard())
            return
        
        elif text == "📢 Рассылка акций":
            user_states[chat_id] = {'state': 'waiting_promo_message'}
            bot.send_message(chat_id, "📢 **Введите текст рассылки:**", parse_mode='Markdown', reply_markup=admin_exit_keyboard())
            return
        
        elif text == "➕ Добавить запись":
            logger.info("🚀 НАЖАТА КНОПКА '➕ Добавить запись'")
            user_states[chat_id] = {'state': 'waiting_chat_id_link'}
            bot.send_message(
                chat_id,
                "📝 **Добавление записи**\n🔗 [@userinfo3bot](https://t.me/userinfo3bot)\nСкопируйте chat_id:",
                parse_mode='Markdown', 
                disable_web_page_preview=True, 
                reply_markup=admin_exit_keyboard()
            )
            return
        
        elif text == "👥 Список клиентов":
            try:
                with db_connection():
                    bookings = Booking.select().order_by(Booking.datetime.desc()).limit(10)
                    if not bookings:
                        bot.send_message(chat_id, "📝 Нет записей", reply_markup=admin_exit_keyboard())
                        return
                    clients_text = "👥 **ПОСЛЕДНИЕ ЗАПИСИ:**\n\n"
                    for booking in bookings:
                        booking_dt = safe_parse_datetime(booking.datetime)
                        dt_str = booking_dt.strftime('%d.%m %H:%M') if booking_dt else "[битая дата]"
                        clients_text += f"• {booking.username or 'N/A'} — {dt_str}\n"
                    bot.send_message(chat_id, clients_text, parse_mode='Markdown', reply_markup=admin_exit_keyboard())
            except Exception as e:
                logger.error(f"Ошибка списка: {e}")
                bot.send_message(chat_id, "❌ Ошибка списка", reply_markup=admin_exit_keyboard())
            return
        
        elif text == "✏️ Редактировать рассылки":
            templates = get_custom_reminders()
            text = f"""✏️ **НАПОМИНАНИЯ:**

📅 *За день:* {templates['day_before'][:80]}...
⏰ *За 2ч:* {templates['two_hours'][:80]}...
🌙 *19:00:* {templates['evening'][:80]}...

👇 Выберите для редактирования"""
            bot.send_message(chat_id, text, reply_markup=reminders_editor_menu(), parse_mode='Markdown')
            return

    # 🔥 #2 АДМИНСКИЕ СОСТОЯНИЯ
    @bot.message_handler(func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and bool(user_states.get(m.chat.id, {}).get('state')))
    def handle_admin_states(message):
        chat_id = message.chat.id
        state = user_states.get(chat_id, {}).get('state')
        
        logger.info(f"🔄 Админ состояние: {state}, текст: '{message.text}'")
        
        if state == 'waiting_chat_id_link':
            chat_id_str = extract_chat_id(message.text)
            if not chat_id_str:
                bot.send_message(chat_id, "❌ chat_id не найден! Пример:\nchat_id: -123456789", reply_markup=admin_exit_keyboard())
                return
            try:
                client_id = int(chat_id_str)
                user_states[chat_id]['chat_id'] = client_id
                user_states[chat_id]['state'] = 'waiting_datetime'
                bot.send_message(chat_id, f"✅ Chat ID: `{client_id}`\n📅 Дата (ДД.ММ.ГГГГ ЧЧ:ММ):", 
                               parse_mode='Markdown', reply_markup=admin_exit_keyboard())
            except ValueError:
                bot.send_message(chat_id, "❌ Неверный chat_id! Должен быть числом.", reply_markup=admin_exit_keyboard())
            return

        elif state == 'waiting_datetime':
            try:
                booking_dt = datetime.strptime(message.text.strip(), '%d.%m.%Y %H:%M')
                if booking_dt < datetime.now():
                    bot.send_message(chat_id, "❌ Дата в прошлом!", reply_markup=admin_exit_keyboard())
                    return

                with db_connection():
                    Booking.create(
                        chat_id=user_states[chat_id]['chat_id'], 
                        username=f"user_{user_states[chat_id]['chat_id']}", 
                        datetime=booking_dt.isoformat()
                    )
                schedule_exact_reminders(bot, user_states[chat_id]['chat_id'], booking_dt)
                
                bot.send_message(chat_id, f"✅ Запись `{user_states[chat_id]['chat_id']}` на {booking_dt.strftime('%d.%m %H:%M')}", 
                               reply_markup=admin_exit_keyboard())
                user_states.pop(chat_id, None)
            except ValueError:
                bot.send_message(chat_id, "❌ Формат: ДД.ММ.ГГГГ ЧЧ:ММ\nПример: 25.12.2025 15:30", reply_markup=admin_exit_keyboard())
            except Exception as e:
                logger.error(f"Ошибка записи: {e}")
                bot.send_message(chat_id, "❌ Ошибка создания записи!", reply_markup=admin_exit_keyboard())
            return

        elif state == 'waiting_promo_message':
            promo_text = message.text
            try:
                with db_connection():
                    clients = Booking.select(Booking.chat_id).distinct()
                    sent, failed = 0, 0
                    for client in clients:
                        try:
                            bot.send_message(client.chat_id, f"🎉 **АКЦИЯ!**\n\n{promo_text}", parse_mode='Markdown')
                            sent += 1
                        except:
                            failed += 1
                bot.send_message(chat_id, f"📢 Рассылка: {sent}✓ {failed}✗", reply_markup=admin_exit_keyboard())
            except Exception as e:
                logger.error(f"Ошибка рассылки: {e}")
                bot.send_message(chat_id, "❌ Ошибка рассылки", reply_markup=admin_exit_keyboard())
            user_states.pop(chat_id, None)
            return

        elif state in ['edit_day_reminder', 'edit_two_hours', 'edit_evening']:
            templates = get_custom_reminders()
            if state == 'edit_day_reminder':
                templates['day_before'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ За день обновлено!", reply_markup=admin_exit_keyboard())
            elif state == 'edit_two_hours':
                templates['two_hours'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ За 2 часа обновлено!", reply_markup=admin_exit_keyboard())
            elif state == 'edit_evening':
                templates['evening'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ 19:00 обновлено!", reply_markup=admin_exit_keyboard())
            user_states.pop(chat_id, None)
            return

    # 🔥 #3 АДМИНСКИЕ CALLBACK
    @bot.callback_query_handler(func=lambda call: call.message.chat.id == settings.ANTON_CHAT_ID)
    def handle_admin_callbacks(call):
        chat_id = call.message.chat.id
        
        logger.info(f"🔄 Админ callback: {call.data}")
        
        if call.data == 'admin_back':
            user_states.pop(chat_id, None)
            bot.edit_message_text("✅ Админ режим завершен", chat_id, call.message.message_id)
            bot.send_message(chat_id, "🔙 Главное меню", reply_markup=back_keyboard())
        elif call.data == 'edit_day':
            templates = get_custom_reminders()
            user_states[chat_id] = {'state': 'edit_day_reminder'}
            bot.edit_message_text(
                f"📅 **За день**\n\n```{templates['day_before']}```\n\nНовый текст:",
                chat_id, call.message.message_id, parse_mode='Markdown'
            )
        elif call.data == 'edit_2h':
            templates = get_custom_reminders()
            user_states[chat_id] = {'state': 'edit_two_hours'}
            bot.edit_message_text(
                f"⏰ **За 2 часа**\n\n```{templates['two_hours']}```\n\nНовый текст:",
                chat_id, call.message.message_id, parse_mode='Markdown'
            )
        elif call.data == 'edit_19':
            templates = get_custom_reminders()
            user_states[chat_id] = {'state': 'edit_evening'}
            bot.edit_message_text(
                f"🌙 **19:00**\n\n```{templates['evening']}```\n\nНовый текст:",
                chat_id, call.message.message_id, parse_mode='Markdown'
            )
        bot.answer_callback_query(call.id)

    # 🔥 #4 ДИАГНОСТИКА - ЛОВИТ ВСЕ СООБЩЕНИЯ ОТ АДМИНА
    @bot.message_handler(func=lambda m: m.chat.id == settings.ANTON_CHAT_ID)
    def debug_admin_messages(message):
        logger.info(f"🔍 АДМИН СООБЩЕНИЕ: '{message.text}' (не обработано другими хендлерами)")

    _admin_handlers_registered = True
    logger.info("✅ АДМИН ХЕНДЛЕРЫ РЕГИСТРИРОВАНЫ - 100% РАБОТАЕТ!")

