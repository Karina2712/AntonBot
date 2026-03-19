import telebot
from telebot import types
import urllib.parse
import requests
from ..config.settings import settings
from ..utils.states import tattoo_search_states
from ..utils.helpers import get_clean_location

PINTEREST_BASE_TEMPLATES = {
    "рука": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B4%D0%BB%D1%8F%20%D1%80%D1%83%D0%BA%D0%B8",
    "предплечье": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20forearm%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D1%80%D0%B5%D0%B4%D0%BF%D0%BB%D0%B5%D1%87%D1%8C%D0%B5",
    "плечо": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20shoulder%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D0%BB%D0%B5%D1%87%D0%BE",
    "грудь": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20chest%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B3%D1%80%D1%83%D0%B4%D0%B8",
    "спина": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20back%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%81%D0%BF%D0%B8%D0%BD%D1%8B",
    "шея": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20neck%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%88%D0%B5%D0%B8",
    "запястье": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20wrist%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B7%D0%B0%D0%BF%D1%8F%D1%81%D1%82%D1%8C%D1%8F",
    "палец": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20finger%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BF%D0%B0%D0%BB%D1%8C%D1%86%D0%B0",
    "нога": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20leg%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BD%D0%BE%D0%B3%D0%B8",
    "бедро": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20thigh%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%B1%D0%B5%D0%B4%D0%B5%D1%80",
    "лодыжка": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20ankle%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D0%BB%D0%BE%D0%B4%D1%8B%D0%B6%D0%BA%D0%B8",
    "ребра": "https://www.pinterest.ru/search/pins/?q={query}%20tattoo%20ribs%20%D1%82%D0%B0%D1%82%D1%83%20%D0%BD%D0%B0%20%D1%80%D0%B5%D0%B1%D0%B5%D1%80"
}


def create_pinterest_url(idea, location):
    idea_encoded = urllib.parse.quote(idea)
    template = PINTEREST_BASE_TEMPLATES.get(location, PINTEREST_BASE_TEMPLATES["рука"])
    query = f"{idea_encoded}%20tattoo"
    return template.format(query=query)


def get_tattoo_meaning(idea, location):
    prompt = f"""Ты эксперт по символике татуировок.
Расскажи кратко (2-3 предложения), что означает татуировка "{idea}" на {location}.
Укажи основные символические значения и эмоции.
Отвечай только текстом значения, без введения."""

    headers = {
        "Authorization": f"Api-Key {settings.YANDEX_GPT_API_KEY}",
        "x-folder-id": settings.YANDEX_GPT_FOLDER_ID,
        "Content-Type": "application/json"
    }

    data = {
        "modelUri": f"gpt://{settings.YANDEX_GPT_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 200
        },
        "messages": [{"role": "user", "text": prompt}]
    }

    try:
        print(f"🤖 Отправка запроса: {idea} на {location}")
        response = requests.post(settings.YANDEX_GPT_URL, headers=headers, json=data, timeout=10)
        print(f"🤖 Status: {response.status_code}")

        # ✅ ИСПРАВЛЕНО: добавлена проверка == 200:
        if response.status_code == 200:
            result = response.json()
            try:
                if 'result' in result and 'alternatives' in result['result'] and result['result']['alternatives']:
                    text = result['result']['alternatives'][0]['message']['text'].strip()
                elif 'result' in result and 'message' in result['result']:
                    text = result['result']['message']['text'].strip()
                else:
                    text = result.get('result', {}).get('text', 'Нет ответа').strip()

                if len(text) > 10:
                    return f"🧠 **Значение:**\n{text[:400]}"
                return "🧠 **Значение:** Символизирует силу и независимость."
            except:
                return "🧠 **Значение:** Красивая и стильная татуировка."
        elif response.status_code == 403:
            return "🚫 *403 Forbidden*"
        elif response.status_code == 429:
            return "⏳ *Лимит запросов*"
        else:
            return f"🤖 *HTTP {response.status_code}*"
    except Exception as e:
        print(f"💥 GPT Error: {e}")
        return "🌐 *Ошибка соединения*"


def process_tattoo_idea(bot, chat_id, idea):
    state_data = tattoo_search_states.get(chat_id, {})
    location = state_data.get('location', 'рука')

    print(f"DEBUG process_tattoo_idea: location='{location}', idea='{idea}'")
    tattoo_search_states.pop(chat_id, None)

    pinterest_url = create_pinterest_url(idea, location)
    meaning = get_tattoo_meaning(idea, location)

    preview_text = f"""🎨 **{idea.upper()} на {location}**

📍 **Место:** {location}
🔍 **Идея:** {idea}

{meaning}

👇 **Pinterest подборка:**"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"🎨 {idea} на {location}", url=pinterest_url))
    markup.row(types.InlineKeyboardButton("🔄 Еще идея", callback_data="new_search"))
    markup.row(types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_menu"))

    bot.send_message(chat_id, preview_text, reply_markup=markup, parse_mode='Markdown')


def show_location_menu(bot, chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤲 Рука", "💪 Предплечье")
    markup.add("👕 Плечо", "☸ Грудь")
    markup.add("🦋 Спина", "🧣 Шея")
    markup.add("⌚ Запястье", "👆 Палец")
    markup.add("🦵 Нога", "🍑 Бедро")
    markup.add("👢 Лодыжка", "🎀 Ребра")
    markup.add("🔙 Назад")
    bot.send_message(chat_id, "📍 **Выберите место:**", reply_markup=markup, parse_mode='Markdown')


def show_tattoo_locations(bot, chat_id, location):
    tattoo_search_states[chat_id] = {"state": "waiting_idea", "location": location}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("🔙 Назад")
    bot.send_message(chat_id,
                     f"🎯 **Место: {location}**\n\n💡 Идея:\n*роза, дракон, волк, лев*\n\n🔍 Только для {location}!",
                     reply_markup=markup, parse_mode='Markdown')
