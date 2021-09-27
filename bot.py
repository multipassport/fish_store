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

HANDLE_MENU, HANDLE_DESCRIPTION = range(2)

_database = None


def get_reply_markup(context):
    access_token = context.bot_data['access_token']

    products = get_products_list(access_token)
    keyboard_buttons = [(product['name'], product['id']) for product in products]
    keyboard = [
        [InlineKeyboardButton(name, callback_data=product_id)]
        for name, product_id in keyboard_buttons
    ]
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    reply_markup = get_reply_markup(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
    return HANDLE_MENU


def press_button(update, context):
    access_token = context.bot_data['access_token']

    query = update.callback_query
    query.answer()

    product = get_product(access_token, query.data)
    text = fetch_product_description(access_token, product)

    photo_id = product['relationships']['main_image']['data']['id']
    photo = get_image_url(access_token, photo_id)

    keyboard = [[InlineKeyboardButton('Назад', callback_data=product['id'])]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_photo(photo, caption=text, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_DESCRIPTION


def return_to_menu(update, context):
    reply_markup = get_reply_markup(context)
    query = update.callback_query
    query.message.reply_text('Choose', reply_markup=reply_markup)    
    return HANDLE_MENU


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
                CallbackQueryHandler(press_button),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(return_to_menu),
            ],
        },
        fallbacks=[MessageHandler(Filters.text, error)],
    )
    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(error)

    updater.start_polling()


if __name__ == '__main__':
    run_bot()
