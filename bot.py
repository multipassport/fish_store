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
    add_product_to_cart,
    get_cart_items,
    fetch_cart_items,
    delete_product_from_cart,
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

HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAIT_FOR_CONTACTS = range(4)

_database = None


def get_reply_markup_for_products(context):
    access_token = context.bot_data['access_token']

    products = get_products_list(access_token)
    products_with_ids = [(product['name'], product['id']) for product in products]
    keyboard = [
        [InlineKeyboardButton(name, callback_data=product_id)]
        for name, product_id in products_with_ids
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def get_reply_markup_for_quantity():
    keyboard = [[
        InlineKeyboardButton('1 kg', callback_data=1),
        InlineKeyboardButton('5 kg', callback_data=5),
        InlineKeyboardButton('10 kg', callback_data=10),
    ],
        [InlineKeyboardButton('Корзина', callback_data='cart')],
        [InlineKeyboardButton('Назад', callback_data='back')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reply_markup_for_cart(context):
    products_with_ids = context.chat_data['products_with_ids']
    keyboard = [
        [InlineKeyboardButton(f'Удалить {name} из корзины', callback_data=product_id)]
        for name, product_id in products_with_ids
    ]
    keyboard.extend((
        [InlineKeyboardButton('В меню', callback_data='back')],
        [InlineKeyboardButton('Оплатить', callback_data='pay')],
    ))
    return InlineKeyboardMarkup(keyboard)


def start(update, context):
    reply_markup = get_reply_markup_for_products(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
    return HANDLE_MENU


def press_button(update, context):
    access_token = context.bot_data['access_token']

    query = update.callback_query
    query.answer()

    product = get_product(access_token, query.data)
    text = fetch_product_description(product)

    photo_id = product['relationships']['main_image']['data']['id']
    photo = get_image_url(access_token, photo_id)

    reply_markup = get_reply_markup_for_quantity()

    context.chat_data['product_id'] = product['id']

    query.message.reply_photo(photo, caption=text, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_DESCRIPTION


def return_to_menu(update, context):
    reply_markup = get_reply_markup_for_products(context)
    query = update.callback_query
    query.message.reply_text('Choose', reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_MENU


def send_callback_data_to_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id

    product_id = context.chat_data['product_id']
    access_token = context.bot_data['access_token']

    weight = int(query.data)
    add_product_to_cart(access_token, product_id, weight, chat_id)
    context.chat_data.pop('product_id')
    return HANDLE_DESCRIPTION


def show_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id

    access_token = context.bot_data['access_token']
    response = get_cart_items(access_token, chat_id)

    message = fetch_cart_items(response)
    context.chat_data['products_with_ids'] = [
        (fish['name'], fish['id']) for fish in response['data']
    ]

    reply_markup = get_reply_markup_for_cart(context)
    query.message.reply_text(message, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_CART


def delete_from_cart(update, context):
    access_token = context.bot_data['access_token']
    query = update.callback_query
    chat_id = query.from_user.id
    product_id = query.data

    delete_product_from_cart(access_token, chat_id, product_id)
    show_cart(update, context)


def ask_for_user_contacts(update, context):
    question = 'Введите ваш e-mail'
    query = update.callback_query
    query.message.reply_text(question)
    return WAIT_FOR_CONTACTS


def respond_to_sent_contact(update, context):
    email = update.message.text
    reply_text = f'Вы прислали эту почту {email}'
    update.message.reply_text(reply_text)

    reply_markup = get_reply_markup_for_products(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
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
            db=0,
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
                CallbackQueryHandler(show_cart, pattern='cart'),
                CallbackQueryHandler(press_button),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(return_to_menu, pattern='back'),
                CallbackQueryHandler(show_cart, pattern='cart'),
                CallbackQueryHandler(send_callback_data_to_cart),
            ],
            HANDLE_CART: [
                CallbackQueryHandler(return_to_menu, pattern='back'),
                CallbackQueryHandler(ask_for_user_contacts, pattern='pay'),
                CallbackQueryHandler(delete_from_cart),
            ],
            WAIT_FOR_CONTACTS: [
                MessageHandler(Filters.text, respond_to_sent_contact),
            ],
        },
        fallbacks=[MessageHandler(Filters.text, error)],
    )
    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(error)

    updater.start_polling()


if __name__ == '__main__':
    run_bot()
