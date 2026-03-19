
import telebot
from telebot import types
from ..config.settings import settings
from ..services.tattoo import process_tattoo_idea
from ..utils.states import tattoo_search_states, user_states


def register_states_handlers(bot: telebot.TeleBot):
    @bot.message_handler(func=lambda message: message.chat.id in tattoo_search_states)
    def handle_tattoo_states(message):
        chat_id = message.chat.id
        state_data = tattoo_search_states.get(chat_id, {})

        if state_data.get('state') == "waiting_location":
            from ..utils.helpers import get_clean_location
            location = get_clean_location(message.text)
            from ..services.tattoo import show_tattoo_locations
            show_tattoo_locations(chat_id, location, bot)
        elif state_data.get('state') == "waiting_idea":
            process_tattoo_idea(chat_id, message.text.strip(), bot)

    @bot.message_handler(func=lambda m: m.chat.id == settings.ANTON_CHAT_ID and m.chat.id in user_states)
    def handle_admin_states(message):
        # Логика состояний админа
        chat_id = message.chat.id
        state = user_states.get(chat_id, {}).get('state')

        try:
            if state == 'waiting_client_chat_id':
                client_chat_id = int(message.text)
                user_states[chat_id] = {'state': 'waiting_date', 'client_chat_id': client_chat_id}
                bot.send_message(chat_id, f"✅ Клиент: {client_chat_id}\n\n📅 Введите дату (2026-03-15):")
            # Другие состояния...
        except ValueError:
            bot.send_message(chat_id, "❌ Неверный формат. Попробуйте снова.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Ошибка: {str(e)}")
