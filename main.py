#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 🔥 RAILWAY ФИКС: добавляем src ВСЕГДА
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))  # Корень проекта

print(f"📂 Рабочая папка: {current_dir}")
print(f"📂 Добавлен src: {src_dir}")

from core.bot import create_bot, run_bot  # ← БЕЗ src.!
from database.database import init_db
from services.reminders import load_reminders

def main():
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("🚀 ✅ Запуск бота...")
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Остановка...")
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        import time
        time.sleep(100)  # Railway не убьет сразу
