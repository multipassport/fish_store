import logging

import telegram


class TelegramBotHandler(logging.Handler):
    def __init__(self, token, chat_id):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        self.bot = telegram.Bot(self.token)

    def emit(self, record):
        self.bot.send_message(chat_id=self.chat_id, text=str(record))
