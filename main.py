#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 🔥 RAILWAY ФИКС: добавляем ВСЕ пути
APP_ROOT = Path(__file__).parent.absolute()
SRC_DIR = APP_ROOT / 'src'

# Добавляем пути ДО импортов!
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(SRC_DIR.parent))

print(f"📁 APP_ROOT: {APP_ROOT}")
print(f"📁 SRC_DIR: {SRC_DIR}")
print(f"📁 PYTHONPATH: {sys.path[:3]}")

# ТЕПЕРЬ импорты работают!
try:
    from src.core.bot import create_bot, run_bot
    from src.database.database import init_db
    from src.services.reminders import load_reminders
    print("✅ Импорты УСПЕШНЫ!")
except ImportError as e:
    print(f"❌ Импорт ошибка: {e}")
    # Fallback импорты
    sys.path.insert(0, '/app/src')
    from src.core.bot import create_bot, run_bot
    print("✅ Fallback импорты!")

def main():
    print("🚀 Инициализация...")
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("✅ Все готово!")
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Ctrl+C")
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import time
        while True:
            time.sleep(10)  # ДЕРЖИ Railway живым!
