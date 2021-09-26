import os
import logging
import redis

from dotenv import load_dotenv
from moltin import access_token, get_products_list, fetch_product_description
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

START, HANDLE_MENU = range(2)

_database = None


def start(update, context):
    products = get_products_list(access_token)
    keyboard_buttons = [(product['name'], product['id']) for product in products]
    keyboard = [
        [InlineKeyboardButton(name, callback_data=product_id)]
        for name, product_id in keyboard_buttons
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Choose', reply_markup=reply_markup
    )
    return HANDLE_MENU


def button(update, context):
    query = update.callback_query
    query.answer()
    message = fetch_product_description(access_token, query.data)

    query.edit_message_text(text=message)
    return START


# def echo(update, context):
#     update.message.reply_text(
#         update.message.text
#     )
#     return ECHO


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('REDIS_PASSWORD')
        database_host = os.getenv('REDIS_HOST')
        database_port = os.getenv('REDIS_PORT')
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password,
            db=0
        )
    return _database


def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def run_bot():
    load_dotenv()
    tg_token = os.getenv('TG_BOT_TOKEN')
    database = get_database_connection()

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HANDLE_MENU: [
                # MessageHandler(Filters.text, echo),
                CallbackQueryHandler(button)
            ],
        },
        fallbacks=[MessageHandler(Filters.text, error)],
    )
    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(error)

    updater.start_polling()


if __name__ == '__main__':
    run_bot()
