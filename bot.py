import os
import logging
import redis

from dotenv import load_dotenv
from log_handler import TelegramBotHandler
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
    create_customer,
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


logger = logging.getLogger(__name__)

HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAIT_FOR_CONTACTS = range(4)

_database = None


def get_reply_markup_for_products(context):
    moltin_headers = context.bot_data['moltin_headers']

    products = get_products_list(**moltin_headers)
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
    moltin_headers = context.bot_data['moltin_headers']

    query = update.callback_query
    query.answer()

    product = get_product(query.data, **moltin_headers)
    text = fetch_product_description(product)

    photo_id = product['relationships']['main_image']['data']['id']
    photo = get_image_url(photo_id, **moltin_headers)

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
    moltin_headers = context.bot_data['moltin_headers']

    weight = int(query.data)
    add_product_to_cart(product_id, weight, chat_id, **moltin_headers)
    context.chat_data.pop('product_id')
    return HANDLE_DESCRIPTION


def show_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id

    moltin_headers = context.bot_data['moltin_headers']
    response = get_cart_items(chat_id, **moltin_headers)

    message = fetch_cart_items(response)
    context.chat_data['products_with_ids'] = [
        (fish['name'], fish['id']) for fish in response['data']
    ]

    reply_markup = get_reply_markup_for_cart(context)
    query.message.reply_text(message, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_CART


def delete_from_cart(update, context):
    moltin_headers = context.bot_data['moltin_headers']
    query = update.callback_query
    chat_id = query.from_user.id
    product_id = query.data

    delete_product_from_cart(chat_id, product_id, **moltin_headers)
    show_cart(update, context)


def ask_for_user_contacts(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    if _database.hget(chat_id, 'user_moltin_id'):
        reply_markup = get_reply_markup_for_products(context)
        query.message.reply_text('Ваша почта уже в базе', reply_markup=reply_markup)
        return HANDLE_MENU
    question = 'Введите ваш e-mail'
    query.message.reply_text(question)
    return WAIT_FOR_CONTACTS


def respond_to_sent_contact(update, context):
    moltin_headers = context.bot_data['moltin_headers']

    tg_message = update.message
    email = tg_message.text
    chat_id = tg_message.from_user.id
    full_name = f'{tg_message.from_user.first_name} {tg_message.from_user.last_name}'

    reply_text = f'Вы прислали эту почту {email}'
    update.message.reply_text(reply_text)

    response = create_customer(full_name, email, **moltin_headers)
    mapping = {'user_moltin_id': response['data']['id']}
    _database.hset(chat_id, mapping=mapping)

    reply_markup = get_reply_markup_for_products(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
    return HANDLE_MENU


def get_database_connection(database_password, database_host, database_port):
    global _database
    if _database is None:
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password,
            db=0,
        )
    return _database


def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    reply_markup = get_reply_markup_for_products(context)
    update.message.reply_text('Произошла ошибка', reply_markup=reply_markup)
    return HANDLE_MENU


def run_bot(tg_token, moltin_headers):
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    context = CallbackContext(dispatcher)
    context.bot_data['moltin_headers'] = moltin_headers

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


def main():
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    tg_token = os.getenv('TG_BOT_TOKEN')
    database_password = os.getenv('REDIS_PASSWORD')
    database_host = os.getenv('REDIS_ENDPOINT')
    database_port = os.getenv('REDIS_PORT')
    logbot_token = os.getenv('TG_LOG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.addHandler(TelegramBotHandler(logbot_token, chat_id))

    _database = get_database_connection(database_password, database_host, database_port)

    access_token = get_bearer_token(client_id, client_secret)
    moltin_headers = {'Authorization': f'Bearer {access_token}'}

    run_bot(tg_token, moltin_headers)


if __name__ == '__main__':
    main()
