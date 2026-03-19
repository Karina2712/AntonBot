#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 🔥 ФИКС: добавляем src в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.bot import create_bot, run_bot
from src.database.database import init_db  # ← АБСОЛЮТНЫЙ импорт!
from src.services.reminders import load_reminders

def main():
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("🚀 ✅ Запуск бота...")
    run_bot()  # ← НЕ передаем bot

if __name__ == "__main__":
    main()
