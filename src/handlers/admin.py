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
from utils.keyboards import back_keyboard, reminders_editor_menu
from utils.states import user_states
from src.database.models import Booking
from services.stats import get_stats

logger = logging.getLogger(__name__)
db = SqliteDatabase('bookings.db')

# ✅ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
_admin_mode_active = set()
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

def _is_admin_active(chat_id):
    global _admin_mode_active
    return bool(user_states.get(chat_id, {}).get('state') or chat_id in _admin_mode_active)

# ✅ КРИТИЧЕСКАЯ ФУНКЦИЯ - БЛОКИРУЕТ КЛИЕНТСКИЕ ХЕНДЛЕРЫ
def is_admin_message(message):
    """ГЛОБАЛЬНАЯ ПРОВЕРКА - для всех клиентских файлов"""
    global _admin_mode_active
    chat_id = message.chat.id
    return chat_id == settings.ANTON_CHAT_ID and (
        message.text in ["📊 Статистика", "📢 Рассылка акций", "➕ Добавить запись", "👥 Список клиентов", "✏️ Редактировать рассылки"] or
        _is_admin_active(chat_id)
    )

def register_admin_handlers(bot: telebot.TeleBot):
    """🚀 АДМИН ХЕНДЛЕРЫ С АБСОЛЮТНЫМ ПРИОРИТЕТОМ"""
    global _admin_handlers_registered
    
    if _admin_handlers_registered:
        logger.warning("⚠️ Админ хендлеры уже зарегистрированы")
        return
    
    logger.info("🔧 Регистрация админ хендлеров...")

    # 🚀 #1 МАКСИМАЛЬНЫЙ ПРИОРИТЕТ - АДМИН КНОПКИ
    @bot.message_handler(func=lambda m: is_admin_message(m))
    def handle_admin_buttons_and_states(message):
        """🎯 ЕДИНЫЙ СУПЕР-ХЕНДЛЕР - ЛОВИТ ВСЁ АДМИНСКОЕ"""
        global _admin_mode_active
        chat_id = message.chat.id
        _admin_mode_active.add(chat_id)
        
        logger.info(f"✅ АДМИН: {message.text}")
        
        # Админ кнопки
        if message.text in ["📊 Статистика", "📢 Рассылка акций", "➕ Добавить запись", "👥 Список клиентов", "✏️ Редактировать рассылки"]:
            if message.text == "📊 Статистика":
                try:
                    stats_text = get_stats()
                    bot.send_message(chat_id, stats_text, parse_mode='Markdown')
                except:
                    bot.send_message(chat_id, "❌ Ошибка статистики")
                    
            elif message.text == "📢 Рассылка акций":
                user_states[chat_id] = {'state': 'waiting_promo_message'}
                bot.send_message(chat_id, "📢 **Введите текст рассылки:**", parse_mode='Markdown')
                
            elif message.text == "➕ Добавить запись":
                user_states[chat_id] = {'state': 'waiting_chat_id_link'}
                bot.send_message(
                    chat_id,
                    "📝 **Добавление записи**\n🔗 [@userinfo3bot](https://t.me/userinfo3bot)\nСкопируйте chat_id:",
                    parse_mode='Markdown', disable_web_page_preview=True
                )
                
            elif message.text == "👥 Список клиентов":
                try:
                    with db_connection():
                        bookings = Booking.select().order_by(Booking.datetime.desc()).limit(10)
                        if not bookings:
                            bot.send_message(chat_id, "📝 Нет записей")
                            return
                        clients_text = "👥 **ЗАПИСИ:**\n\n"
                        for booking in bookings:
                            booking_dt = safe_parse_datetime(booking.datetime)
                            dt_str = booking_dt.strftime('%d.%m %H:%M') if booking_dt else "[битая дата]"
                            clients_text += f"• {booking.username or 'N/A'} — {dt_str}\n"
                        bot.send_message(chat_id, clients_text, parse_mode='Markdown')
                except Exception as e:
                    logger.error(f"Ошибка списка: {e}")
                    bot.send_message(chat_id, "❌ Ошибка списка")
                    
            elif message.text == "✏️ Редактировать рассылки":
                templates = get_custom_reminders()
                text = f"""✏️ **НАПОМИНАНИЯ:**

📅 *За день:* {templates['day_before'][:80]}...
⏰ *За 2ч:* {templates['two_hours'][:80]}...
🌙 *19:00:* {templates['evening'][:80]}...

👇 Выберите для редактирования"""
                bot.send_message(chat_id, text, reply_markup=reminders_editor_menu(), parse_mode='Markdown')
            return

        # Админ состояния
        state_data = user_states.get(chat_id, {})
        state = state_data.get('state')
        if not state:
            return

        logger.info(f"🔄 Состояние: {state}")

        if state == 'waiting_chat_id_link':
            chat_id_str = extract_chat_id(message.text)
            if not chat_id_str:
                bot.send_message(chat_id, "❌ chat_id не найден!")
                return
            try:
                client_id = int(chat_id_str)
                state_data['chat_id'] = client_id
                state_data['state'] = 'waiting_datetime'
                user_states[chat_id] = state_data
                bot.send_message(chat_id, f"✅ Chat ID: `{client_id}`\n📅 Дата (ДД.ММ.ГГГГ ЧЧ:ММ):", parse_mode='Markdown')
            except:
                bot.send_message(chat_id, "❌ Неверный chat_id!")
            return

        elif state == 'waiting_datetime':
            try:
                booking_dt = datetime.strptime(message.text.strip(), '%d.%m.%Y %H:%M')
                if booking_dt < datetime.now():
                    bot.send_message(chat_id, "❌ Дата в прошлом!")
                    return

                with db_connection():
                    Booking.create(chat_id=state_data['chat_id'], username=f"user_{state_data['chat_id']}", datetime=booking_dt.isoformat())
                schedule_exact_reminders(bot, state_data['chat_id'], booking_dt)
                bot.send_message(chat_id, f"✅ Запись `{state_data['chat_id']}` на {booking_dt.strftime('%d.%m %H:%M')}")
                user_states.pop(chat_id, None)
                _admin_mode_active.discard(chat_id)
            except ValueError:
                bot.send_message(chat_id, "❌ Формат: ДД.ММ.ГГГГ ЧЧ:ММ")
            except Exception as e:
                logger.error(f"Ошибка записи: {e}")
                bot.send_message(chat_id, "❌ Ошибка!")
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
                    bot.send_message(chat_id, f"📢 Рассылка: {sent}✓ {failed}✗")
            except Exception as e:
                logger.error(f"Ошибка рассылки: {e}")
                bot.send_message(chat_id, "❌ Ошибка рассылки")
            user_states.pop(chat_id, None)
            _admin_mode_active.discard(chat_id)
            return

        elif state in ['edit_day_reminder', 'edit_two_hours', 'edit_evening']:
            templates = get_custom_reminders()
            if state == 'edit_day_reminder':
                templates['day_before'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ За день обновлено!")
            elif state == 'edit_two_hours':
                templates['two_hours'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ За 2 часа обновлено!")
            elif state == 'edit_evening':
                templates['evening'] = message.text
                save_custom_reminders(templates)
                bot.send_message(chat_id, "✅ 19:00 обновлено!")
            
            user_states.pop(chat_id, None)
            _admin_mode_active.discard(chat_id)
            return

    # 🚀 #2 Callback кнопки
    @bot.callback_query_handler(
        func=lambda call: call.message.chat.id == settings.ANTON_CHAT_ID and 
        call.data in ['edit_day', 'edit_2h', 'edit_19']
    )
    def handle_reminder_edit(call):
        global _admin_mode_active
        _admin_mode_active.add(call.message.chat.id)
        templates = get_custom_reminders()
        
        if call.data == 'edit_day':
            user_states[call.message.chat.id] = {'state': 'edit_day_reminder'}
            bot.edit_message_text(
                f"📅 **За день**\n\n```{templates['day_before']}```\n\nНовый текст:",
                call.message.chat.id, call.message.message_id, parse_mode='Markdown'
            )
        elif call.data == 'edit_2h':
            user_states[call.message.chat.id] = {'state': 'edit_two_hours'}
            bot.edit_message_text(
                f"⏰ **За 2 часа**\n\n```{templates['two_hours']}```\n\nНовый текст:",
                call.message.chat.id, call.message.message_id, parse_mode='Markdown'
            )
        elif call.data == 'edit_19':
            user_states[call.message.chat.id] = {'state': 'edit_evening'}
            bot.edit_message_text(
                f"🌙 **19:00**\n\n```{templates['evening']}```\n\nНовый текст:",
                call.message.chat.id, call.message.message_id, parse_mode='Markdown'
            )
        bot.answer_callback_query(call.id)

    _admin_handlers_registered = True
    logger.info("✅ АДМИН ХЕНДЛЕРЫ РЕГИСТРИРОВАНЫ - ПРИОРИТЕТ МАКСИМАЛЬНЫЙ!")

