import telebot
from telebot import types
from datetime import datetime, timedelta
import re
import threading
import time
import json
import os
import logging
from config.settings import settings
from utils.keyboards import back_keyboard, reminders_editor_menu
from utils.states import user_states
from src.database.models import Booking
from services.stats import get_stats
from peewee import SqliteDatabase
from contextlib import contextmanager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# База данных
db = SqliteDatabase('data/anton_bot.db')

@contextmanager
def db_connection():
    """Контекстный менеджер для БД"""
    db.connect()
    try:
        yield
    finally:
        db.close()

reminder_scheduler = {}
REMINDERS_FILE = "custom_reminders.json"

def load_custom_reminders():
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки напоминаний: {e}")
    return {
        'day_before': """👋 Привет!\\n\\nНапоминаю тебе о записи: *{datetime}*\\n\\nПодготовься:\\n✅ Выспись\\n✅ Прими душ\\n✅ Не пей алкоголь\\n✅ Побрей место тату\\n✅ Плотно покушай\\n✅ Возьми вкусняшки с собой 😋""",
        'two_hours': """👋 Привет!\\n\\nЯ жду тебя сегодня: *{datetime}* 🎨""",
        'evening': """🎉 Поздравляю тебя с татуировкой!\\n\\n💡 **Уход после тату:**\\n• Не расчесывай\\n• Не замачивай в воде\\n• Используй крем 2-3 раза в день\\n• Не посещай сауну/баню 2 недели"""
    }

def save_custom_reminders(templates):
    try:
        os.makedirs(os.path.dirname(REMINDERS_FILE) or '.', exist_ok=True)
        with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения напоминаний: {e}")
        return False

def get_custom_reminders():
    return load_custom_reminders()

def safe_parse_datetime(date_obj_or_str):
    """Фикс для всех форматов Peewee datetime"""
    try:
        # Peewee возвращает datetime объекты напрямую!
        if hasattr(date_obj_or_str, 'strftime') and callable(date_obj_or_str.strftime):
            return date_obj_or_str
            
        date_str = str(date_obj_or_str).strip()
        
        # Игнорируем битые форматы типа '2026-03-17 (Tue)'
        if '(Tue)' in date_str or '(Mon)' in date_str or '(Wed)' in date_str:
            logger.warning(f"Пропуск битой даты с днем недели: {date_str}")
            return None
            
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S', 
            '%Y-%m-%d %H:%M',
            '%d.%m.%Y %H:%M',
            '%Y-%m-%d',
            '%d.%m.%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        logger.warning(f"Невозможно распарсить дату: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Критическая ошибка парсинга даты {date_obj_or_str}: {e}")
        return None

def extract_chat_id(text):
    patterns = [
        r'chat_id:\s*(-?\d+)',
        r'"id"\s*:\s*(-?\d+)',
        r'(-?\d+)\s*(chat|id)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def schedule_exact_reminders(bot, chat_id, booking_dt):
    global reminder_scheduler
    templates = get_custom_reminders()

    def send_day():
        try:
            bot.send_message(
                chat_id,
                templates['day_before'].format(
                    datetime=booking_dt.strftime('%d.%m.%Y %H:%M')
                ),
                parse_mode='Markdown'
            )
            logger.info(f"✅ Напоминание за день отправлено пользователю {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания за день {chat_id}: {e}")

    def send_2h():
        try:
            bot.send_message(
                chat_id,
                templates['two_hours'].format(
                    datetime=booking_dt.strftime('%d.%m.%Y %H:%M')  # ИСПРАВЛЕНО: %m вместо %M
                ),
                parse_mode='Markdown'
            )
            logger.info(f"✅ Напоминание за 2 часа отправлено пользователю {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминания за 2 часа {chat_id}: {e}")

    def send_19():
        try:
            bot.send_message(chat_id, templates['evening'], parse_mode='Markdown')
            logger.info(f"✅ Вечернее напоминание отправлено пользователю {chat_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки вечернего напоминания {chat_id}: {e}")

    # Отменяем старые напоминания БЕЗОБРАЗНО
    for key in [f"{chat_id}_day", f"{chat_id}_2h", f"{chat_id}_19"]:
        if key in reminder_scheduler:
            try:
                reminder_scheduler[key].cancel()
                del reminder_scheduler[key]
            except:
                pass

    now = datetime.now()
    
    # За день в 9:00
    send_time_day = (booking_dt - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    if send_time_day > now:
        sec_day = max(0.1, (send_time_day - now).total_seconds())
        reminder_scheduler[f"{chat_id}_day"] = threading.Timer(sec_day, send_day)
        reminder_scheduler[f"{chat_id}_day"].start()
        logger.info(f"⏰ Запланировано напоминание за день для {chat_id} на {send_time_day}")

    # За 2 часа
    send_time_2h = booking_dt - timedelta(hours=2)
    if send_time_2h > now:
        sec_2h = max(0.1, (send_time_2h - now).total_seconds())
        reminder_scheduler[f"{chat_id}_2h"] = threading.Timer(sec_2h, send_2h)
        reminder_scheduler[f"{chat_id}_2h"].start()
        logger.info(f"⏰ Запланировано напоминание за 2ч для {chat_id} на {send_time_2h}")

    # Вечер 19:00
    send_time_19 = booking_dt.replace(hour=19, minute=0, second=0, microsecond=0)
    if send_time_19 > now:
        sec_19 = max(0.1, (send_time_19 - now).total_seconds())
        reminder_scheduler[f"{chat_id}_19"] = threading.Timer(sec_19, send_19)
        reminder_scheduler[f"{chat_id}_19"].start()
        logger.info(f"⏰ Запланировано вечернее напоминание для {chat_id} на {send_time_19}")

def check_existing_reminders(bot):
    """Проверка существующих записей при запуске бота"""
    logger.info("🔍 Проверка существующих напоминаний...")
    try:
        with db_connection():
            bookings = Booking.select()
            now = datetime.now()
            valid_count = 0
            
            for booking in bookings:
                booking_dt = safe_parse_datetime(booking.datetime)
                if booking_dt is None:
                    logger.warning(f"⚠️ Пропуск записи {booking.chat_id} - битая дата: {booking.datetime}")
                    continue
                
                valid_count += 1
                if booking_dt > now:
                    logger.info(f"📅 Перепланировываю напоминания для {booking.chat_id} на {booking_dt}")
                    schedule_exact_reminders(bot, booking.chat_id, booking_dt)
                else:
                    logger.info(f"⏰ Запись {booking.chat_id} уже прошла: {booking_dt}")
            
            logger.info(f"✅ Проверено записей: {valid_count}, пропущено битых дат")
                    
    except Exception as e:
        logger.error(f"❌ Ошибка проверки напоминаний: {e}")

def cleanup_scheduler():
    """Очистка завершившихся таймеров"""
    while True:
        time.sleep(300)  # 5 минут
        for key in list(reminder_scheduler.keys()):
            try:
                if hasattr(reminder_scheduler[key], 'is_alive') and not reminder_scheduler[key].is_alive():
                    del reminder_scheduler[key]
            except:
                pass

def register_admin_handlers(bot: telebot.TeleBot):
    """Регистрация всех админ хендлеров"""
    # ПРОВЕРКА НАПОМИНАНИЙ ПРИ ЗАПУСКЕ
    check_existing_reminders(bot)
    
    # Кнопки-команды (работают всегда)
    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "📊 Статистика"
    )
    def show_stats(message):
        try:
            stats_text = get_stats()
            bot.send_message(
                message.chat.id,
                stats_text,
                reply_markup=back_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка статистики: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка получения статистики", reply_markup=back_keyboard())

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "📢 Рассылка акций"
    )
    def promo_broadcast_start(message):
        user_states[message.chat.id] = {'state': 'waiting_promo_message'}
        bot.send_message(
            message.chat.id,
            "📢 **РАССЫЛКА АКЦИЙ**\\n\\nВведите текст сообщения для рассылки:",
            parse_mode='Markdown'
        )

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "➕ Добавить запись"
    )
    def add_booking_start(message):
        user_states[message.chat.id] = {'state': 'waiting_chat_id_link'}
        bot.send_message(
            message.chat.id,
            "📝 **Добавление записи**\\n\\n🔗 Перейдите к [@userinfo3bot](https://t.me/userinfo3bot)\\n\\n🤖 Отправьте ему /start и скопируйте **chat_id** сюда:",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "👥 Список клиентов"
    )
    def show_clients_list(message):
        with db_connection():
            try:
                bookings = Booking.select().order_by(Booking.datetime.desc()).limit(10)
                if not bookings:
                    bot.send_message(message.chat.id, "📝 Нет записей", reply_markup=back_keyboard())
                    return
                clients_text = "👥 **ЗАПИСИ КЛИЕНТОВ:**\\n\\n"
                for booking in bookings:
                    booking_dt = safe_parse_datetime(booking.datetime)
                    if booking_dt:
                        clients_text += f"• {booking.username or 'N/A'} — {booking_dt.strftime('%d.%m.%Y %H:%M')}\\n"
                    else:
                        clients_text += f"• {booking.username or 'N/A'} — [битая дата]\\n"
                bot.send_message(
                    message.chat.id,
                    clients_text,
                    reply_markup=back_keyboard(),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Ошибка получения списка клиентов: {e}")
                bot.send_message(message.chat.id, "❌ Ошибка получения списка", reply_markup=back_keyboard())

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "✏️ Редактировать рассылки"
    )
    def show_reminders_editor(message):
        templates = get_custom_reminders()
        text = f"""✏️ **РЕДАКТИРОВАНИЕ НАПОМИНАНИЙ**

📅 *За день (9:00):* {templates['day_before'][:100]}...
⏰ *За 2 часа:* {templates['two_hours'][:100]}...
🌙 *19:00:* {templates['evening'][:100]}...

👇 Нажмите кнопку для редактирования"""
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=reminders_editor_menu(),
            parse_mode='Markdown'
        )

    @bot.message_handler(
        func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.text == "🔙 Клиентское меню"
    )
    def back_to_client_menu(message):
        try:
            from handlers.client import send_welcome
            send_welcome(message)
        except Exception as e:
            logger.error(f"Ошибка клиентского меню: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка меню", reply_markup=back_keyboard())

    # Универсальный хендлер для состояний
    @bot.message_handler(
        func=lambda m: (
            m.chat.id == settings.ANTON_CHAT_ID and
            m.text not in [
                "📊 Статистика", "📢 Рассылка акций", "➕ Добавить запись",
                "👥 Список клиентов", "✏️ Редактировать рассылки", "🔙 Клиентское меню"
            ]
        )
    )
    def handle_admin_states(message):
        state_data = user_states.get(message.chat.id, {})
        state = state_data.get('state')
        templates = get_custom_reminders()

        # Редактирование напоминаний
        if state == 'edit_day_reminder':
            templates['day_before'] = message.text
            if save_custom_reminders(templates):
                bot.send_message(message.chat.id, "✅ Напоминание за день обновлено!", reply_markup=back_keyboard())
            del user_states[message.chat.id]
            return
        elif state == 'edit_two_hours':
            templates['two_hours'] = message.text
            if save_custom_reminders(templates):
                bot.send_message(message.chat.id, "✅ Напоминание за 2 часа обновлено!", reply_markup=back_keyboard())
            del user_states[message.chat.id]
            return
        elif state == 'edit_evening':
            templates['evening'] = message.text
            if save_custom_reminders(templates):
                bot.send_message(message.chat.id, "✅ Напоминание 19:00 обновлено!", reply_markup=back_keyboard())
            del user_states[message.chat.id]
            return

        # Кнопки редактирования
        text_lower = message.text.lower()
        if "редактировать день" in text_lower:
            user_states[message.chat.id] = {'state': 'edit_day_reminder'}
            bot.send_message(
                message.chat.id,
                f"📅 **За день**\\n\\n```{templates['day_before']}```\\n\\nНовый текст:",
                parse_mode='Markdown'
            )
            return
        elif "редактировать 2 часа" in text_lower:
            user_states[message.chat.id] = {'state': 'edit_two_hours'}
            bot.send_message(
                message.chat.id,
                f"⏰ **За 2 часа**\\n\\n```{templates['two_hours']}```\\n\\nНовый текст:",
                parse_mode='Markdown'
            )
            return
        elif "редактировать 19" in text_lower:
            user_states[message.chat.id] = {'state': 'edit_evening'}
            bot.send_message(
                message.chat.id,
                f"🌙 **19:00**\\n\\n```{templates['evening']}```\\n\\nНовый текст:",
                parse_mode='Markdown'
            )
            return

        # Добавление записи
        if state == 'waiting_chat_id_link':
            chat_id_str = extract_chat_id(message.text)
            if not chat_id_str:
                bot.send_message(message.chat.id, "❌ Не найден chat_id! Попробуйте еще раз.")
                return
            try:
                chat_id = int(chat_id_str)
                state_data['chat_id'] = chat_id
                state_data['state'] = 'waiting_datetime'
                user_states[message.chat.id] = state_data
                bot.send_message(
                    message.chat.id,
                    f"✅ Chat ID: `{chat_id}`\\n\\n📅 Дата (ДД.ММ.ГГГГ ЧЧ:ММ):",
                    parse_mode='Markdown'
                )
            except ValueError:
                bot.send_message(message.chat.id, "❌ Неверный chat_id!")

        elif state == 'waiting_datetime':
            try:
                booking_dt = datetime.strptime(message.text.strip(), '%d.%m.%Y %H:%M')
                if booking_dt < datetime.now():
                    bot.send_message(message.chat.id, "❌ Дата в прошлом!")
                    return
                
                with db_connection():
                    Booking.create(
                        chat_id=state_data['chat_id'],
                        username=f"user_{state_data['chat_id']}",
                        datetime=booking_dt
                    )
                
                schedule_exact_reminders(bot, state_data['chat_id'], booking_dt)
                bot.send_message(
                    message.chat.id,
                    f"✅ Запись: `{state_data['chat_id']}` на {booking_dt.strftime('%d.%m %H:%M')}",
                    parse_mode='Markdown',
                    reply_markup=back_keyboard()
                )
                del user_states[message.chat.id]
                
            except ValueError:
                bot.send_message(message.chat.id, "❌ Формат: ДД.ММ.ГГГГ ЧЧ:ММ")
            except Exception as e:
                logger.error(f"Ошибка создания записи: {e}")
                bot.send_message(message.chat.id, "❌ Ошибка создания записи!")

        elif state == 'waiting_promo_message':
            promo_text = message.text
            with db_connection():
                try:
                    clients = Booking.select(Booking.chat_id).distinct()
                    sent, failed = 0, 0
                    for client in clients:
                        try:
                            bot.send_message(
                                client.chat_id,
                                f"🎉 **АКЦИЯ!**\\n\\n{promo_text}",
                                parse_mode='Markdown'
                            )
                            sent += 1
                        except:
                            failed += 1
                    
                    bot.send_message(
                        message.chat.id,
                        f"📢 Рассылка: {sent}✓ {failed}✗",
                        reply_markup=back_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Ошибка рассылки: {e}")
                    bot.send_message(message.chat.id, "❌ Ошибка рассылки!")
            
            del user_states[message.chat.id]

def start_reminder_scheduler(bot):
    """Запуск планировщика напоминаний"""
    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()
    logger.info("✅ Планировщик напоминаний запущен")

    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()
    logger.info("✅ Планировщик напоминаний запущен")

