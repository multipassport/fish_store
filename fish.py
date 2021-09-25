import os
import requests

from dotenv import load_dotenv


def get_bearer_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    moltin_keys = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=moltin_keys)
    response.raise_for_status()
    return response.json().get('access_token')


def get_products_list(access_token):
    url = 'https://api.moltin.com/v2/products'
    header = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=header)
    response.raise_for_status()
    return response.json()


def add_product_to_cart():
    url = 'https://api.moltin.com/v2/carts/:reference/items'


if __name__ == '__main__':
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    access_token = get_bearer_token(client_id, client_secret)

    products = get_products_list(access_token)
