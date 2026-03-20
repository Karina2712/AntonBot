import sys
import os
from pathlib import Path

APP_ROOT = Path(__file__).parent.absolute()
SRC_DIR = APP_ROOT / 'src'
sys.path.insert(0, str(SRC_DIR))  # /app/src
sys.path.insert(0, str(APP_ROOT)) # /app

print(f"📁 APP_ROOT: {APP_ROOT}")
print(f"📁 SRC_DIR: {SRC_DIR}")

from core.bot import create_bot
from database.database import init_db
from services.reminders import load_reminders
from handlers.admin import register_admin_handlers, start_reminder_scheduler  # ✅ ИМПОРТ

print("✅ Импорты работают!")

def main():
    os.makedirs("data", exist_ok=True)
    init_db()
    load_reminders()
    print("🚀 Запуск бота...")
    
    # ✅ СОЗДАЕМ БОТА
    bot = create_bot()
    
    # ✅ РЕГИСТРИРУЕМ ХЕНДЛЕРЫ И ПЛАНИРОВЩИК
    register_admin_handlers(bot)
    start_reminder_scheduler(bot)
    
    # ✅ ПРАВИЛЬНЫЙ polling БЕЗ 'clean'
    print("✅ Запуск безопасного polling...")
    bot.infinity_polling(
        none_stop=True,    # не останавливается при ошибках
        interval=1,        # пауза между запросами
        timeout=30         # таймаут long polling
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import time
        while True: 
            time.sleep(10)
