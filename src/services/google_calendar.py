import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from ..config.settings import settings

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Положите в корень проекта


def get_calendar_service():
    """Создает подключение к Google Calendar"""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)


def get_free_days(days_ahead=7):
    """Возвращает 5 ближайших свободных дней"""
    service = get_calendar_service()
    now = datetime.utcnow().isoformat() + 'Z'
    end_date = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

    # Получаем события
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end_date,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    busy_dates = set()

    # Собираем занятые даты
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if start:
            date_only = start.split('T')[0]
            busy_dates.add(date_only)

    # Находим свободные дни
    free_days = []
    for i in range(1, days_ahead + 1):
        date_obj = datetime.now().date() + timedelta(days=i)
        date_str = date_obj.strftime('%Y-%m-%d')

        if date_str not in busy_dates:
            day_name = date_obj.strftime('%A')[:3].capitalize()
            free_days.append(f"{date_str} ({day_name})")
            if len(free_days) >= 5:
                break

    return free_days if free_days else ["Нет свободных дней"]


def send_to_anton(bot, chat_id, username, telegram_id, username_telegram, selected_date):
    """Отправляет данные Антону"""
    message = f"""🆕 **НОВАЯ ЗАПИСЬ!**

👤 *{username}*
🆔 `{telegram_id}`
💬 @{username_telegram}
📅 *{selected_date}*

📞 Связаться с клиентом?"""

    try:
        bot.send_message(settings.ANTON_CHAT_ID, message, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"Ошибка отправки Антону: {e}")
        return False