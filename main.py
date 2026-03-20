
import sys
import os
from pathlib import Path

# 🔥 RAILWAY ФИКС
APP_ROOT = Path(__file__).parent.absolute()
SRC_DIR = APP_ROOT / 'src'
sys.path.insert(0, str(SRC_DIR))  # /app/src
sys.path.insert(0, str(APP_ROOT)) # /app

print(f"📁 APP_ROOT: {APP_ROOT}")
print(f"📁 SRC_DIR: {SRC_DIR}")

# 🔥 БЕЗ src. ПРЕФИКСА!
from core.bot import create_bot, run_bot
from database.database import init_db
from services.reminders import load_reminders

print("✅ Импорты работают!")

def main():
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("🚀 Запуск бота...")
    run_bot()
register_admin_handlers(bot)
start_reminder_scheduler(bot)
bot.infinity_polling(none_stop=True, interval=0, timeout=20)
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 {e}")
        import time
        while True: time.sleep(10)

