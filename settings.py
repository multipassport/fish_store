import os
from dotenv import load_dotenv


load_dotenv()


def get_moltin_credentials():
	client_id = os.getenv('CLIENT_ID')
	client_secret = os.getenv('CLIENT_SECRET')
	return client_id, client_secret


def get_redis_credentials():
    database_password = os.getenv('REDIS_PASSWORD')
    database_host = os.getenv('REDIS_ENDPOINT')
    database_port = os.getenv('REDIS_PORT')
    return database_password, database_host, database_port


def get_telegram_credentials():
    tg_token = os.getenv('TG_BOT_TOKEN')
    logbot_token = os.getenv('TG_LOG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    return tg_token, logbot_token, chat_id
