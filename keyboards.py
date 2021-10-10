from moltin import create_headers, get_products_list
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_reply_markup_for_products(context):
    moltin_headers = create_headers(context)

    products = get_products_list(**moltin_headers)
    products_with_ids = [(product['name'], product['id']) for product in products]
    keyboard = [
        [InlineKeyboardButton(name, callback_data=product_id)]
        for name, product_id in products_with_ids
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def get_reply_markup_for_quantity():
    keyboard = [[
        InlineKeyboardButton('1 kg', callback_data=1),
        InlineKeyboardButton('5 kg', callback_data=5),
        InlineKeyboardButton('10 kg', callback_data=10),
    ],
        [InlineKeyboardButton('Корзина', callback_data='cart')],
        [InlineKeyboardButton('Назад', callback_data='back')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_reply_markup_for_cart(context):
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
