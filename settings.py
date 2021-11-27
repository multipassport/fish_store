import os
from dotenv import load_dotenv


load_dotenv()

_token = None
_token_expire_time = 0
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
