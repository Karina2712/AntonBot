
import os
from peewee import (
    SqliteDatabase, Model, CharField, IntegerField, DateTimeField, TextField
)
from datetime import datetime, timezone

os.makedirs("data", exist_ok=True)
db = SqliteDatabase('data/anton_bot.db')

class BaseModel(Model):
    class Meta:
        database = db

class UserSearchHistory(BaseModel):
    chat_id = IntegerField(unique=True)
    username = CharField(null=True)
    searches = TextField(default='[]')
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

class Booking(BaseModel):
    booking_id = CharField(primary_key=True)
    chat_id = IntegerField()
    username = CharField(null=True)
    datetime = CharField()
    time = CharField()
    status = CharField(default='confirmed')
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

def init_db():
    db.connect()
    db.create_tables([UserSearchHistory, Booking], safe=True)
    print("✅ База данных создана: data/anton_bot.db")
    db.close()