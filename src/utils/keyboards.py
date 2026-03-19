# src/utils/keyboards.py (ОБЪЕДИНЕНИЕ ВСЕХ)
from telebot import types
from datetime import datetime, timedelta

def client_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🎨 Записаться на тату", "💡 Найти идею тату")
    markup.add("💬 Задать вопрос Антону")
    markup.add("ℹ️ Информация", "📞 Контакты")
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Статистика", "📢 Рассылка акций")
    markup.add("➕ Добавить запись", "👥 Список клиентов")
    markup.add("✏️ Редактировать рассылки", "🔙 Клиентское меню")
    return markup

def location_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤲 Рука", "💪 Предплечье")
    markup.add("👕 Плечо", "☸ Грудь")
    markup.add("🦋 Спина", "🧣 Шея")
    markup.add("⌚ Запястье", "👆 Палец")
    markup.add("🦵 Нога", "🍑 Бедро")
    markup.add("👢 Лодыжка", "🎀 Ребра")
    markup.add("🔙 Назад")
    return markup

def booking_calendar_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    today = datetime.now().date()
    for i in range(14):
        date = today + timedelta(days=i)
        if date.weekday() != 6:  # нет воскресенья
            date_str = date.strftime("%d.%m")
            markup.add(f"📅 {date_str}")
            if markup.keyboard and len(markup.keyboard) >= 5:
                break
    markup.add("🔙 Главное меню")
    return markup

def back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Назад")
    return markup

def reminders_editor_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📩 Напоминание за 24ч", "⏰ Напоминание за 2ч")
    markup.add("🙏 Благодарность 19:00", "🔙 Назад")
    return markup
