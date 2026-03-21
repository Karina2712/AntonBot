from telebot import types
from config.settings import settings
from utils.keyboards import (
    client_menu, booking_calendar_menu, location_menu, admin_menu
)
import requests
import urllib.parse
import json


user_states = {}

# Pinterest + YandexGPT настройки
YANDEX_GPT_API_KEY = settings.YANDEX_GPT_API_KEY
YANDEX_GPT_FOLDER_ID = settings.YANDEX_GPT_FOLDER_ID
YANDEX_GPT_URL = settings.YANDEX_GPT_URL

LOCATION_MAP = {
    "🤲 Рука": "рука", "💪 Предплечье": "предплечье", "👕 Плечо": "плечо",
    "☸ Грудь": "грудь", "🦋 Спина": "спина", "🧣 Шея": "шея",
    "⌚ Запястье": "запястье", "👆 Палец": "палец", "🦵 Нога": "нога",
    "🍑 Бедро": "бедро", "👢 Лодыжка": "лодыжка", "🎀 Ребра": "ребра"
}

PINTEREST_BASE_TEMPLATES = {
    "рука": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B4%D0%BB%D1%8F%20%D1%80%D1%83%D0%BA%D0%B8",
    "предплечье": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20forearm%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D1%80%D0%B5%D0%B4%D0%BF%D0%BB%D0%B5%D1%87%D1%8C%D0%B5",
    "плечо": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20shoulder%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D0%BB%D0%B5%D1%87%D0%BE",
    "грудь": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20chest%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B3%D1%80%D1%83%D0%B4%D0%B8",
    "спина": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20back%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%81%D0%BF%D0%B8%D0%BD%D1%8B",
    "шея": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20neck%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%88%D0%B5%D0%B8",
    "запястье": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20wrist%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B7%D0%B0%D0%BF%D1%8F%D1%81%D1%82%D1%8C%D1%8F",
    "палец": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20finger%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D0%B0%D0%BB%D1%8C%D1%86%D0%B0",
    "нога": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20leg%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BD%D0%BE%D0%B0%D0%B3%D0%B8",
    "бедро": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20thigh%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B1%D0%B5%D0%B4%D0%B5%D1%80",
    "лодыжка": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20ankle%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BB%D0%BE%D0%B4%D1%8B%D0%B6%D0%BA%D0%B8",
    "ребра": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20ribs%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%80%D0%B5%D0%B1%D0%B5%D1%80"
}


def get_clean_location(button_text):
    """Получить чистое название локации"""
    return next((clean for full, clean in LOCATION_MAP.items() if full == button_text), "рука")


def create_pinterest_url(idea, location):
    """Создать Pinterest ссылку"""
    idea_encoded = urllib.parse.quote(idea)
    template = PINTEREST_BASE_TEMPLATES.get(location, PINTEREST_BASE_TEMPLATES["рука"])
    return template.format(query=idea_encoded)


def get_tattoo_meaning(idea, location):
    """Получить значение тату от YandexGPT"""
    if not YANDEX_GPT_API_KEY:
        return "🧠 Значение: Красивая и стильная татуировка."

    prompt = f"""Ты эксперт по символике татуировок.
Расскажи кратко (2-3 предложения), что означает татуировка "{idea}" на {location}.
Укажи основные символические значения и эмоции.
Отвечай только текстом значения, без введения."""

    headers = {
        "Authorization": f"Api-Key {YANDEX_GPT_API_KEY}",
        "x-folder-id": YANDEX_GPT_FOLDER_ID,
        "Content-Type": "application/json"
    }

    data = {
        "modelUri": f"gpt://{YANDEX_GPT_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 200},
        "messages": [{"role": "user", "text": prompt}]
    }

    try:
        response = requests.post(YANDEX_GPT_URL, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            text = result['result']['alternatives'][0]['message']['text'].strip()
            return f"🧠 Значение:\n{text[:300]}"
        return "🧠 Значение: Символизирует силу и независимость."
    except:
        return "🧠 Значение: Красивая и стильная татуировка."


def process_tattoo_idea(bot, chat_id, idea, location):
    """Обработать идею тату - Pinterest + Значение"""
    pinterest_url = create_pinterest_url(idea, location)
    meaning = get_tattoo_meaning(idea, location)

    preview_text = f"""🎨 {idea.upper()} на {location}

📍 Место: {location}
🔍 Идея: {idea}

{meaning}

👇 Pinterest подборка:"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🎨 {idea} на {location}", url=pinterest_url))
    markup.row(types.InlineKeyboardButton("🔄 Еще идея", callback_data=f"new_search_{location}"))
    markup.row(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_menu"))

    bot.send_message(chat_id, preview_text, reply_markup=markup)


def show_contacts(chat_id, bot):
    """📞 КОНТАКТЫ с КЛИКАБЕЛЬНЫМ НОМЕРОМ ДЛЯ ЗВОНКА"""
    markup = types.InlineKeyboardMarkup(row_width=1)

    #  КНОПКА ЗВОНКА - номер телефона кликабельный!
    markup.add(types.InlineKeyboardButton("📞 Позвонить Антону +79373036332",
                                          url="https://t.me/+79373036332"))
    markup.add(types.InlineKeyboardButton("💬 Telegram Антона", url="https://t.me/Antonkonturufa"))
    markup.add(types.InlineKeyboardButton("🔗 VK Антона", url="https://vk.com/anton.kontur"))
    markup.add(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_menu"))

    # ДОПОЛНИТЕЛЬНО: текст с кликабельным номером
    contact_text = """📱 **Контакты Антона:**

☎️ **+79373036332** - звони прямо сейчас!

👇 Или используй кнопки ниже:"""

    bot.send_message(chat_id, contact_text, reply_markup=markup, parse_mode='Markdown')


def test_client_menu():
    """Гарантированно рабочая клавиатура для теста"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🎨 Записаться на тату", "💡 Найти идею тату")
    markup.add("💬 Задать вопрос Антону")
    markup.add("ℹ️ Информация", "📞 Контакты")
    return markup


def register_client_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        chat_id = message.chat.id
        user_name = message.from_user.first_name or "Клиент"
        print(f"DEBUG: /start от {chat_id}")

        for state_dict in [user_states]:
            state_dict.pop(chat_id, None)

        if chat_id == settings.ANTON_CHAT_ID:
            bot.send_message(chat_id, "🔧 ПАНЕЛЬ АДМИНА", reply_markup=admin_menu())
        else:
            bot.send_message(chat_id, f"👋 Привет, {user_name}! Выбери действие:",
                             reply_markup=client_menu())

    @bot.message_handler(func=lambda message: True)
    def client_handler(message):
        chat_id = message.chat.id
        text = message.text
        user_name = message.from_user.first_name or "Клиент"
        print(f"DEBUG: '{text}' от {chat_id}")

        #  ВОПРОСЫ АНТОНУ(ПРИОРИТЕТ)
        if user_states.get(chat_id) == 'question':
            question_text = f"💬 {user_name}: {text}"
            bot.send_message(settings.ANTON_CHAT_ID, question_text)
            bot.send_message(chat_id, "✅ Отправлено Антону!")
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "👋 Что дальше?", reply_markup=client_menu())
            return

        #  СОСТОЯНИЕ ЗАПИСИ (ПРОВЕРКА НА "ГЛАВНОЕ МЕНЮ" И "НАЗАД")
        if user_states.get(chat_id) == 'date':
            # 🔥 ИСПРАВЛЕНО: проверка кнопок возврата ПЕРЕД обработкой даты
            if text in ["🏠 Главное меню", "Главное меню", "🔙 Назад"]:
                user_states.pop(chat_id, None)
                bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())
                return

            selected_date = text.replace("📅 ", "").strip()
            username = message.from_user.username or f"ID{chat_id}"
            anton_message = f"НОВАЯ ЗАПИСЬ!\n\n👤 {user_name}\n🆔 @{username}\n📅 {selected_date}\n💡 Свяжется для выбора времени"
            bot.send_message(settings.ANTON_CHAT_ID, anton_message)
            bot.send_message(chat_id,
                             f"ЗАПИСЬ НА {selected_date} ПЕРЕДАНА АНТОНУ!\n\n👨‍🎨 Антон свяжется с тобой для выбора времени")
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "👋 Что дальше?", reply_markup=client_menu())
            return

        #  TATTOO SEARCH
        if chat_id in user_states and isinstance(user_states[chat_id], dict) and 'tattoo' in user_states[chat_id]:
            state_data = user_states[chat_id]['tattoo']
            if state_data['state'] == 'waiting_location':

                if text == "🔙 Назад":
                    del user_states[chat_id]
                    bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())
                    return

                clean_location = get_clean_location(text)
                user_states[chat_id]['tattoo'] = {'state': 'waiting_idea', 'location': clean_location}
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                markup.add("🔙 Назад")
                bot.send_message(chat_id,
                                 f"🎯 Место: {clean_location}\n\n💡 Идея:\n(напиши свою идею: например роза,дркон и тд)\n\n🔍 Только для {clean_location}!",
                                 reply_markup=markup)
                return
            elif state_data['state'] == 'waiting_idea':

                if text == "🔙 Назад":
                    del user_states[chat_id]
                    bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())
                    return

                idea = text.strip()
                location = state_data['location']
                process_tattoo_idea(bot, chat_id, idea, location)
                del user_states[chat_id]
                return

        if text == "💬 Задать вопрос Антону":
            user_states[chat_id] = 'question'
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            markup.add("🔙 Назад")
            bot.send_message(chat_id,
                             f"💬 *Напиши свой вопрос Антону*\n\n📝 Пример: 'Какой уход за тату?'\n🕐 Антон ответит в ближайшее время!",
                             reply_markup=markup)
            return

        if text == "🎨 Записаться на тату":
            user_states[chat_id] = 'date'
            bot.send_message(chat_id, "📅 ВЫБЕРИ СВОБОДНУЮ ДАТУ:\n\n💡 График: ПН-ЧТ 10-20, ПТ 10-22, СБ 12-20",
                             reply_markup=booking_calendar_menu())
            return

        if text == "💡 Найти идею тату":
            user_states[chat_id] = {'tattoo': {'state': 'waiting_location'}}
            bot.send_message(chat_id, "📍 Выберите место:", reply_markup=location_menu())
            return

        if text == "ℹ️ Информация":
            bot.send_message(chat_id,
                             "🏪 **АНТОН ТАТУ-МАСТЕР**\n👨‍🎨 Опыт: 7+ лет\n📍 Уфа, Пр. Октября(ориентир Семья)\n💰 Цены от 4000₽",
                             parse_mode='Markdown')
            bot.send_message(chat_id, "👇 Вернуться в меню:", reply_markup=client_menu())
            return

        if text == "📞 Контакты":
            show_contacts(chat_id, bot)
            return

        if text in ["🔙 Назад", "🏠 Главное меню", "Главное меню"]:
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())
            return

        bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())
