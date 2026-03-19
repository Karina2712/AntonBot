from datetime import datetime
import json
import os
from ..database.models import db, UserSearchHistory


def update_user_stats(chat_id, username):
    """Обновляет статистику пользователя (заглушка для совместимости)"""
    stats_file = "stats.json"
    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        except:
            pass

    stats[chat_id] = {
        'name': username,
        'last_active': str(datetime.now()),
        'interactions': stats.get(chat_id, {}).get('interactions', 0) + 1
    }

    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except:
        pass


def get_clean_location(button_text):
    """Очищает название места татуировки"""
    LOCATION_MAP = {
        "🤲 Рука": "рука", "💪 Предплечье": "предплечье", "👕 Плечо": "плечо",
        "☸ Грудь": "грудь", "🦋 Спина": "спина", "🧣 Шея": "шея",
        "⌚ Запястье": "запястье", "👆 Палец": "палец", "🦵 Нога": "нога",
        "🍑 Бедро": "бедро", "👢 Лодыжка": "лодыжка", "🎀 Ребра": "ребра"
    }

    return LOCATION_MAP.get(button_text, "рука")


def get_user_search_history(chat_id, limit=10):
    """Получает историю поисков из БД"""
    try:
        db.connect()
        user_record = UserSearchHistory.get_or_create(chat_id=chat_id)[0]
        history = json.loads(user_record.searches) if user_record.searches else []
        db.close()
        return history[:limit]
    except Exception as e:
        print(f"Ошибка истории: {e}")
        if db.is_connection_usable():
            db.close()
        return []

    def validate_chat_id(chat_id_text):
        """Проверяет chat_id"""
        try:
            return int(chat_id_text) > 0
        except ValueError:
            return False

    def validate_date(date_text):
        """Проверяет формат даты YYYY-MM-DD"""
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def validate_time(time_text):
        """Проверяет формат времени HH:MM"""
        try:
            datetime.strptime(time_text, '%H:%M')
            return True
        except ValueError:
            return False
# Добавить в конец:
LOCATION_MAP = {
    "🤲 Рука": "рука", "💪 Предплечье": "предплечье",
    "👕 Плечо": "плечо", "☸ Грудь": "грудь",
    # ... все из monolith
}

def get_clean_location(button_text):
    return LOCATION_MAP.get(button_text, "рука")
