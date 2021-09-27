import os
import logging
import redis

from dotenv import load_dotenv
from moltin import (
    get_bearer_token,
    get_products_list,
    fetch_product_description,
    get_image_url,
    get_product,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

START, HANDLE_MENU = range(2)

_database = None


def start(update, context):
    access_token = context.bot_data['access_token']

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
    context.chat_data['message_to_delete'] = update['message']['message_id']
    return HANDLE_MENU


def button(update, context):
    access_token = context.bot_data['access_token']
    query = update.callback_query
    query.answer()
    product = get_product(access_token, query.data)
    text = fetch_product_description(access_token, product)
    photo_id = product['relationships']['main_image']['data']['id']
    photo = get_image_url(access_token, photo_id)
    query.message.reply_photo(photo, caption=text)
    query.message.delete()
    return START


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

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    tg_token = os.getenv('TG_BOT_TOKEN')

    database = get_database_connection()

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    context = CallbackContext(dispatcher)
    context.bot_data['access_token'] = get_bearer_token(client_id, client_secret)

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
