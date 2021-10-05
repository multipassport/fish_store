import glob
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


def add_product_to_cart(access_token, product_id, quantity, chat_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        },
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart(access_token, chat_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(access_token, chat_id):
    url = f'https://api.moltin.com/v2/carts/{chat_id}/items'
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


def create_file(access_token, filepath):
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    with open(filepath, 'rb') as file:
        files = {
            'file': file,
            'public': True
        }
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
    return response.json()


def get_file_ids(access_token):
    url = 'https://api.moltin.com/v2/files'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return [description['id'] for description in response.json()['data']]


def link_product_with_image(access_token, product_id, image_id):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
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


def get_image_url(access_token, image_id):
    url = f'https://api.moltin.com/v2/files/{image_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


if __name__ == '__main__':
    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    product_id = '3b76a3c5-a505-46bc-9924-fbf719903599'

    images_pathes = glob.glob('./fishes/*')
    access_token = get_bearer_token(client_id, client_secret)
    print(access_token)

    # for image_path in images_pathes:
    #     create_file(access_token, image_path)
    products = get_products_list(access_token)
    # print(get_file_ids(access_token))
    print(products)
    # link_product_with_image(
    #     access_token,
    #     '3b76a3c5-a505-46bc-9924-fbf719903599',
    #     'd9633aad-c19e-42cd-a1d8-3c26dab44fe4'
    # )

    # product = products[0]
