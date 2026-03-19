import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TOKEN = os.getenv("TOKEN")
    ANTON_CHAT_ID = int(os.getenv("ANTON_CHAT_ID", "496910417"))
    YANDEX_GPT_API_KEY = os.getenv("YANDEX_GPT_API_KEY")
    YANDEX_GPT_FOLDER_ID = os.getenv("YANDEX_GPT_FOLDER_ID")
    YANDEX_GPT_URL = os.getenv("YANDEX_GPT_URL", "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")

    @classmethod
    def get_settings(cls):
        return cls()

settings = Settings.get_settings()