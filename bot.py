import os
import logging
import redis

from dotenv import load_dotenv
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

START, ECHO = range(2)

_database = None


def start(update, context):
    # quiz_keyboard = [['option1', 'option2'],
    #                  ['option3']]
    keyboard = [[InlineKeyboardButton('Option1', callback_data='1'),
                 InlineKeyboardButton('Option2', callback_data='2')],

                [InlineKeyboardButton('Option3', callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Choose', reply_markup=reply_markup
    )
    return ECHO


def button(update, context):
    query = update.callback_query
    query.answer()

    query.edit_message_text(text=f'Selected option: {query.data}')


def echo(update, context):
    update.message.reply_text(
        update.message.text
    )
    return ECHO


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
            ECHO: [
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
