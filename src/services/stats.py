import json
import os
from src.database.models import db, Booking, UserSearchHistory  # ← АБСОЛЮТНЫЙ!

def get_stats():
    stats_file = "stats.json"
    stats = {}
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        except:
            pass

    total_users = len(stats)
    total_interactions = sum(s.get('interactions', 0) for s in stats.values())

    total_bookings = 0
    total_searches = 0
    try:
        db.connect()
        total_bookings = Booking.select().where(Booking.status == 'confirmed').count()
        total_searches = UserSearchHistory.select().count()
        db.close()
    except:
        pass

    return f"""📊 **СТАТИСТИКА**

👥 Пользователей: {total_users}
💬 Взаимодействий: {total_interactions}
📅 Записей: {total_bookings}
🔍 Поисков идей: {total_searches}"""
