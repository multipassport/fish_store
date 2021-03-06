from moltin import get_products_list
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_products_reply_markup(context):
    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']

    products = get_products_list(client_id, client_secret)

    products_with_ids = [(product['name'], product['id']) for product in products]
    keyboard = [
        [InlineKeyboardButton(name, callback_data=product_id)]
        for name, product_id in products_with_ids
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def get_quantity_reply_markup():
    keyboard = [[
        InlineKeyboardButton('1 kg', callback_data=1),
        InlineKeyboardButton('5 kg', callback_data=5),
        InlineKeyboardButton('10 kg', callback_data=10),
    ],
        [InlineKeyboardButton('Корзина', callback_data='cart')],
        [InlineKeyboardButton('Назад', callback_data='back')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cart_reply_markup(context):
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
