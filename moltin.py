import requests
import time


_token = None
_token_expire_time = 0


def get_bearer_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    moltin_keys = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=moltin_keys)
    response.raise_for_status()
    moltin_responce = response.json()

    token_expire_time = moltin_responce['expires']
    access_token = moltin_responce['access_token']
    return access_token, token_expire_time


def get_actual_token(client_id, client_secret):
    global _token
    global _token_expire_time

    if time.time() > _token_expire_time:
        _token, _token_expire_time = get_bearer_token(client_id, client_secret)
    return _token


def get_products_list(client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = 'https://api.moltin.com/v2/products'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_moltin_cart(product_id, quantity, chat_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    headers_for_post = dict(headers)
    headers_for_post['Content-Type'] = 'application/json'
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        },
    }
    response = requests.post(url, headers=headers_for_post, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart(chat_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/carts/{chat_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(chat_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(product_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/products/{product_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def fetch_product_description(response):
    name = response['name']
    price = f'{response["meta"]["display_price"]["with_tax"]["formatted"]} per kg'
    stock = f'{response["meta"]["stock"]["level"]}kg on stock'
    description = response['description']
    return '\n'.join((name, price, stock, description))


def fetch_cart_items(response):
    message = ''
    for fish in response['data']:
        name = fish['name']
        description = fish['description']
        quantity = fish['quantity']
        price_per_unit =f'{fish["meta"]["display_price"]["with_tax"]["unit"]["formatted"]} per kg'
        position_price = fish['meta']['display_price']['with_tax']['value']['formatted']
        position_quantity_and_price = f'{quantity}kg in cart for {position_price}'
        position = '\n'.join((name, description, price_per_unit, position_quantity_and_price))
        message += f'{position}\n\n'
    total = response['meta']['display_price']['with_tax']['formatted']
    message += f'Total: {total}'
    return message


def create_file(filepath, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = 'https://api.moltin.com/v2/files'

    with open(filepath, 'rb') as file:
        files = {
            'file': file,
            'public': True
        }
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
    return response.json()


def get_file_ids(client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = 'https://api.moltin.com/v2/files'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return [description['id'] for description in response.json()['data']]


def link_product_with_image(product_id, image_id, client_id, client_secret):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    access_token = get_actual_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    payload = {
        'data': {
            'type': 'main_image',
            'id': image_id,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_image_url(image_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/files/{image_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def delete_product_from_cart(chat_id, product_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items/{product_id}'
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer(name, email, client_id, client_secret):
    url = 'https://api.moltin.com/v2/customers'
    access_token = get_actual_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        },
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 409:
        return None
    response.raise_for_status()
    return response.json()


def get_customer(chat_id, client_id, client_secret):
    access_token = get_actual_token(client_id, client_secret)
    headers = {'Authorization': f'Bearer {access_token}'}

    url = f'https://api.moltin.com/v2/customers/{chat_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
