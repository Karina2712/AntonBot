import sys
import os
from pathlib import Path
import time

# ✅ ФИКС sys.path - ОДИН раз
APP_ROOT = Path(__file__).parent.absolute()
SRC_DIR = APP_ROOT / 'src'
sys.path.insert(0, str(APP_ROOT))
sys.path.insert(0, str(SRC_DIR))

print(f"📁 APP_ROOT: {APP_ROOT}")
print(f"📁 SRC_DIR: {SRC_DIR}")

from core.bot import create_bot
from database.database import init_db
from services.reminders import load_reminders
from handlers.admin import register_admin_handlers, start_reminder_scheduler

print("✅ Импорты работают!")

def main():
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("🚀 Запуск бота...")
    
    bot = create_bot()
    register_admin_handlers(bot)
    start_reminder_scheduler(bot)
    
    print("✅ Запуск безопасного polling...")
    
    # ✅ НАДЕЖНЫЙ POLLING ДЛЯ RAILWAY
    while True:
        try:
            bot.polling(
                none_stop=True,
                interval=1,
                timeout=20
            )
        except Exception as e:
            print(f"🔄 Polling ошибка, перезапуск: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        while True:
            time.sleep(10)
