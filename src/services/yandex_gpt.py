import requests
from ..config.settings import settings


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
        response = requests.post(settings.YANDEX_GPT_URL, headers=headers, json=data, timeout=20)

        if response.status_code == 200:
            result = response.json()
            text = result['result']['alternatives'][0]['message'][
                'text'].strip() if 'result' in result else "Нет ответа"
            return f"🧠 **Значение:**\n{text[:400]}" if len(
                text) > 10 else "🧠 **Значение:** Символизирует силу и независимость."
        else:
            return f"🤖 *HTTP {response.status_code}*"
    except Exception:
        return "🌐 *Ошибка соединения*"
