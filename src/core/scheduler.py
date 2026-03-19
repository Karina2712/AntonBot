
from apscheduler.schedulers.background import BackgroundScheduler
from ..services.reminders import check_reminders

class Scheduler:
    def __init__(self, bot, settings):
        self.scheduler = BackgroundScheduler()
        self.bot = bot
        self.scheduler.add_job(
            func=lambda: check_reminders(self.bot),
            trigger="interval",
            minutes=5
        )
        print("✅ Планировщик запущен")

    def start(self):
        self.scheduler.start()