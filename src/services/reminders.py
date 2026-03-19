

from ..database.models import Booking

import json
def load_reminders():
    global REMINDERS_TEMPLATES
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            REMINDERS_TEMPLATES.update(json.load(f))
    except FileNotFoundError:
        pass


# Глобальные шаблоны напоминаний
REMINDERS_TEMPLATES = {
    "reminder_6h": "👋 *Привет!* Не забудь о записи на тату через 6 часов!\\n\\n💡 *Рекомендации:*\\n• Приди за 15 минут\\n• Не ешь жирное\\n• Возьми воду\\n• Сделай свежий душ",
    "reminder_2h": "⏰ *Напоминание о записи через 2 часа!*\\n\\n📅 Время: {time}\\n📍 Пр. Октября\\n👨‍🎨 Антон ждет тебя!",
    "thanks_19": "🙏 *Спасибо, что пришел на сеанс!*\\n\\n💖 *Уход за тату:*\\n• Снимай пленку через 2-4 часа\\n• Мой теплой водой + антисептик\\n• Мажь Бепантен 2-3 раза в день\\n• НЕ чеши! 2 недели"
}


def check_reminders(bot):
    now = datetime.now()

    try:
        from ..database.models import db
        db.connect()
        bookings = Booking.select().where(Booking.status == 'confirmed')
        for booking in bookings:
            booking_time = datetime.strptime(booking.datetime, '%Y-%m-%d %H:%M')

            if now >= (booking_time - timedelta(hours=6)) and now < (booking_time - timedelta(hours=5, minutes=55)):
                send_reminder(bot, booking.chat_id, 'reminder_6h', {'time': booking.time})
            elif now >= (booking_time - timedelta(hours=2)) and now < (booking_time - timedelta(hours=1, minutes=55)):
                send_reminder(bot, booking.chat_id, 'reminder_2h', {'time': booking.time})
        db.close()
    except Exception as e:
        print(f"Ошибка проверки напоминаний: {e}")


def send_reminder(bot, chat_id, template_key, data):
    template = REMINDERS_TEMPLATES.get(template_key, "")
    message = template.format(**data)
    try:
        bot.send_message(chat_id, message, parse_mode='Markdown')
        print(f"✅ Напоминание {template_key} отправлено пользователю {chat_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки напоминания: {e}")


def show_reminders_editor(chat_id, bot):  # ← ЭТОГО НЕ ХВАЛО!
    from ..utils.keyboards import reminders_editor_menu
    text = f"""✏️ **РЕДАКТИРОВАНИЕ РАССЫЛОК**

📩 *За 6 часов:* {REMINDERS_TEMPLATES['reminder_6h'][:100]}...
⏰ *За 2 часа:* {REMINDERS_TEMPLATES['reminder_2h'][:100]}...
🙏 *19:00:* {REMINDERS_TEMPLATES['thanks_19'][:100]}..."""
    bot.send_message(chat_id, text, reply_markup=reminders_editor_menu(), parse_mode='Markdown')


def save_reminder_edit(chat_id, bot, key, new_text):  # ← ЭТОГО НЕ ХВАЛО!
    REMINDERS_TEMPLATES[key] = new_text
    bot.send_message(chat_id, f"✅ *Сохранено!*\\n\\n{new_text[:100]}...")
    show_reminders_editor(chat_id, bot)

import json
from datetime import datetime, timedelta

REMINDERS_TEMPLATES = {
    "reminder_6h": "👋 *Привет!* Не забудь...",
    # ... дефолтные
}

def load_reminders():
    global REMINDERS_TEMPLATES
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            REMINDERS_TEMPLATES.update(json.load(f))
    except FileNotFoundError:
        pass

def save_reminders():
    with open('reminders.json', 'w', encoding='utf-8') as f:
        json.dump(REMINDERS_TEMPLATES, f, ensure_ascii=False, indent=2)
