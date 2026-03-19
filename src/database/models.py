
from peewee import Model, CharField, IntegerField, DateTimeField, TextField, SqliteDatabase
from datetime import datetime
import os

# Создаем db локально, чтобы избежать циклического импорта
DB_PATH = 'data/anton_bot.db'
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = SqliteDatabase(DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class UserSearchHistory(BaseModel):
    chat_id = IntegerField(unique=True, index=True)
    username = CharField(max_length=100, null=True)
    searches = TextField()
    created_at = DateTimeField(default=lambda: datetime.now())
    updated_at = DateTimeField(default=lambda: datetime.now())

class Booking(BaseModel):
    booking_id = CharField(primary_key=True)
    chat_id = IntegerField()
    username = CharField(max_length=100, null=True)
    datetime = CharField(max_length=50)
    time = CharField(max_length=10)
    status = CharField(max_length=20, default='confirmed')
    created_at = DateTimeField(default=lambda: datetime.now())