from telebot import types
from ..config.settings import settings

def client_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("🎨 Записаться на тату")
    markup.add("💡 Найти идею тату")
    markup.add("📜 Моя история")
    markup.add("💬 Задать вопрос Антону", "ℹ️ Информация", "📞 Контакты")
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

def idea_keyboard():  # ← НОВЫЙ ФУНКЦИЯ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("🔙 Назад")
    return markup

def back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("🔙 Назад")
    return markup

def reminders_editor_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("📩 Напоминание за 6ч", "⏰ Напоминание за 2ч")
    markup.add("🙏 Благодарность 19:00", "🔙 Назад")
    return markup

def contacts_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔙 Назад")
    return markup
