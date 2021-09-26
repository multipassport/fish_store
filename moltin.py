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
    return response.json()['data']


def add_product_to_cart(access_token, product_id):
    url = 'https://api.moltin.com/v2/carts/mltpass/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': 1,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart(access_token):
    url = 'https://api.moltin.com/v2/carts/mltpass'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(access_token, product_id):
    url = os.path.join('https://api.moltin.com/v2/products/', product_id)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()['data']


def fetch_product_description(access_token, product_id):
    response = get_product(access_token, product_id)
    name = response['name']
    price = f'{response["meta"]["display_price"]["with_tax"]["formatted"]} per kg'
    stock = f'{response["meta"]["stock"]["level"]}kg on stock'
    description = response['description']
    return '\n'.join((name, price, stock, description))


load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
access_token = get_bearer_token(client_id, client_secret)
products = get_products_list(access_token)


if __name__ == '__main__':
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    product_id = '3b76a3c5-a505-46bc-9924-fbf719903599'

    access_token = get_bearer_token(client_id, client_secret)

    products = get_products_list(access_token)
    product = products[0]
