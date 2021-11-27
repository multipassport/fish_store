import logging
import redis

from keyboards import (
    get_products_reply_markup,
    get_quantity_reply_markup,
    get_cart_reply_markup,
)
from log_handler import TelegramBotHandler
from moltin import (
    get_bearer_token,
    fetch_product_description,
    get_image_url,
    get_product,
    add_product_to_moltin_cart,
    get_cart_items,
    fetch_cart_items,
    delete_product_from_cart,
    create_customer,
    create_headers,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from settings import get_redis_credentials, get_telegram_credentials


logger = logging.getLogger(__name__)

HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAIT_FOR_CONTACTS = range(4)


def start(update, context):
    reply_markup = get_products_reply_markup(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
    return HANDLE_MENU


def show_product_description(update, context):
    query = update.callback_query
    query.answer()

    product = get_product(query.data)
    text = fetch_product_description(product)

    photo_id = product['relationships']['main_image']['data']['id']
    photo = get_image_url(photo_id)

    reply_markup = get_quantity_reply_markup()

    context.chat_data['product_id'] = product['id']

    query.message.reply_photo(photo, caption=text, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_DESCRIPTION


def return_to_menu(update, context):
    reply_markup = get_products_reply_markup(context)
    query = update.callback_query
    query.message.reply_text('Choose', reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_MENU


def send_item_to_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id

    product_id = context.chat_data['product_id']
    weight = int(query.data)
    add_product_to_moltin_cart(product_id, weight, chat_id)
    context.chat_data.pop('product_id')
    return HANDLE_DESCRIPTION


def show_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id

    response = get_cart_items(chat_id)

    message = fetch_cart_items(response)
    context.chat_data['products_with_ids'] = [
        (fish['name'], fish['id']) for fish in response['data']
    ]

    reply_markup = get_cart_reply_markup(context)
    query.message.reply_text(message, reply_markup=reply_markup)
    query.message.delete()
    return HANDLE_CART


def delete_from_cart(update, context):
    query = update.callback_query
    chat_id = query.from_user.id
    product_id = query.data

    delete_product_from_cart(chat_id, product_id)
    show_cart(update, context)


def ask_for_user_contacts(update, context):
    database = context.bot_data['database']

    query = update.callback_query
    chat_id = query.from_user.id

    if database.hget(chat_id, 'user_moltin_id'):
        reply_markup = get_products_reply_markup(context)
        query.message.reply_text('Ваша почта уже в базе', reply_markup=reply_markup)
        return HANDLE_MENU
    question = 'Введите ваш e-mail'
    query.message.reply_text(question)
    return WAIT_FOR_CONTACTS


def respond_to_sent_contact(update, context):
    database = context.bot_data['database']

    tg_message = update.message
    email = tg_message.text
    chat_id = tg_message.from_user.id
    full_name = f'{tg_message.from_user.first_name} {tg_message.from_user.last_name}'

    reply_text = f'Вы прислали эту почту {email}'
    update.message.reply_text(reply_text)

    response = create_customer(full_name, email)
    mapping = {'user_moltin_id': response['data']['id']}

    database.hset(chat_id, mapping=mapping)

    reply_markup = get_products_reply_markup(context)
    update.message.reply_text('Choose', reply_markup=reply_markup)
    return HANDLE_MENU


def get_database_connection(database_password, database_host, database_port):
    return redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password,
        db=0,
    )


def handle_error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    return HANDLE_MENU


def run_bot(tg_token, database):
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    context = CallbackContext(dispatcher)

    context.bot_data['database'] = database

    conversation = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(show_cart, pattern='cart'),
                CallbackQueryHandler(show_product_description),
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(return_to_menu, pattern='back'),
                CallbackQueryHandler(show_cart, pattern='cart'),
                CallbackQueryHandler(send_item_to_cart),
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
        fallbacks=[MessageHandler(Filters.text, handle_error)],
    )
    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(handle_error)

    updater.start_polling()


def main():
    tg_token, logbot_token, chat_id = get_telegram_credentials()
    redis_credentials = get_redis_credentials()

    database = get_database_connection(*redis_credentials)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger.addHandler(TelegramBotHandler(logbot_token, chat_id))

    run_bot(tg_token, database)


if __name__ == '__main__':
    main()
