import telebot
from telebot import types
from ..utils.keyboards import client_menu
from ..utils.helpers import get_user_search_history


def register_callback_handlers(bot):
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        chat_id = call.message.chat.id

        if call.data == "show_history":
            history = get_user_search_history(chat_id)
            if not history:
                bot.answer_callback_query(call.id, "📝 История пуста")
                return

            history_text = "📜 **ВАША ИСТОРИЯ ПОИСКОВ**:\n\n"
            for i, search in enumerate(history[:10], 1):
                history_text += f"{i}. 🎨 *{search['idea']}* на {search['location']}\n"

            bot.send_message(chat_id, history_text, parse_mode='Markdown')

        elif call.data == "back_menu":
            bot.send_message(chat_id, "👋 Выбери действие:", reply_markup=client_menu())