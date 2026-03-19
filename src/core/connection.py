
import os
from peewee import SqliteDatabase
from contextlib import contextmanager

os.makedirs("data", exist_ok=True)
db = SqliteDatabase('data/anton_bot.db')

def init_db():
    from .models import UserSearchHistory, Booking
    db.connect()
    db.create_tables([UserSearchHistory, Booking], safe=True)
    print("✅ База данных создана: data/anton_bot.db")
    db.close()

@contextmanager
def get_db():
    db.connect()
    try:
        yield db
    finally:
        db.close()

def connect_db():
    db.connect()

def close_db():
    if db.is_connection_usable():
        db.close()
