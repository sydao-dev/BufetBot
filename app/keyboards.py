from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from datetime import datetime, timedelta

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests import get_categories, get_category_item, get_item, get_lyceums, get_orders, get_order_by_code, get_order

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Зробити замовлення')],
                                     [KeyboardButton(text='Інше'),
                                      KeyboardButton(text='Обрати інший ліцей')]],
                            resize_keyboard=True,
                            input_field_placeholder='Оберіть один з пунктів меню...')

admin = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Змінити наявність')],
                                     [KeyboardButton(text='Активні замовлення')]],
                            resize_keyboard=True,
                            input_field_placeholder='Оберіть один з пунктів меню...')

shifts = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1 зміна', callback_data='shifts_1'),
    InlineKeyboardButton(text='2 зміна', callback_data='shifts_2')]])

async def intervals(shift):
    keyboard = InlineKeyboardBuilder()
    
    for i in range(1, 7):
        keyboard.add(InlineKeyboardButton(text=f'Перерва №{i}', callback_data=f'interval_{shift}_{i}'))
        
    return keyboard.adjust(2).as_markup()
    
async def lyceums():
    all_lyceums = await get_lyceums()
    keyboard = InlineKeyboardBuilder()
    
    for lyceum in all_lyceums:
        keyboard.add(InlineKeyboardButton(text=lyceum.name, callback_data=f'lyceum_{lyceum.id}'))
    
    return keyboard.adjust(1).as_markup()

async def admin_lyceums():
    all_lyceums = await get_lyceums()
    keyboard = InlineKeyboardBuilder()
    
    for lyceum in all_lyceums:
        keyboard.add(InlineKeyboardButton(text=lyceum.name, callback_data=f'admin_lyceum_{lyceum.id}'))
    
    return keyboard.adjust(1).as_markup()

async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Головне меню', callback_data='to_main'))
    return keyboard.adjust(2).as_markup()

async def admin_categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(text=category.name, callback_data=f'admin_category_{category.id}'))
    keyboard.add(InlineKeyboardButton(text='Головне меню', callback_data='admin_to_main_'))
    return keyboard.adjust(2).as_markup()


async def admin_items(category_id, user_id):
    all_items = await get_category_item(category_id, user_id)
    keyboard = InlineKeyboardBuilder()
    
    for item in all_items:
        keyboard.add(InlineKeyboardButton(text=item.name, callback_data=f"admin_items_{item.id}"))
    keyboard.add(InlineKeyboardButton(text='Головне меню', callback_data='admin_to_main_'))
    return keyboard.adjust(1).as_markup()

async def more_info(item_id):
    item_info = await get_item(item_id)
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Більше інформації', callback_data=f'more_info_{item_info.id}'))
    
    return keyboard.adjust(1).as_markup()

async def item_data(item_id):
    item_info = await get_item(item_id)
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Додати до кошика ✅', callback_data=f'add_item_{item_info.id}'))
    keyboard.add(InlineKeyboardButton(text='Повернутись назад', callback_data=f'category_{item_info.category}'))
    
    return keyboard.adjust(1).as_markup()

async def req_shop(user_id):
    keyboard = InlineKeyboardBuilder()
    
    order = await get_order(user_id)
    
    keyboard.add(InlineKeyboardButton(text='Оплатити корзину ✅', callback_data=f'cart_buy_{order.id}'))
    keyboard.add(InlineKeyboardButton(text='Додати інші товари 🛒', callback_data='add_to_cart_category'))
    keyboard.add(InlineKeyboardButton(text='Скасувати ❌', callback_data=f'delete_cart_{order.id}'))
    
    return keyboard.adjust(1).as_markup()

async def count(item_id):
    item_info = await get_item(item_id)
    keyboard = InlineKeyboardBuilder()
    item_count = 5
    for item_count in range(1, item_count + 1):
        keyboard.add(InlineKeyboardButton(text=f'{item_count}', callback_data=f'add_to_cart_item_{item_info.id}_{item_count}'))
    
    keyboard.add(InlineKeyboardButton(text='Скасувати ❌', callback_data=f'category_{item_info.category}'))
    
    return keyboard.adjust(item_count, 1).as_markup()
    
async def buy(order_id):
    
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Оплатити ✅', callback_data = f'buy_{order_id}'))
    keyboard.add(InlineKeyboardButton(text='Скасувати ❌', callback_data=f'delete_cart_{order_id}'))
    
    return keyboard.adjust(1).as_markup()
    
async def buy_cart(pay_url):
    
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Оплатити ✅', url = pay_url))
    
    return keyboard.adjust(1).as_markup()

async def all_order(lyceum):
    
    orders = await get_orders(lyceum)
    
    keyboard = InlineKeyboardBuilder()
    
    for order in orders:
        keyboard.add(InlineKeyboardButton(text=f'Код №{order.code}', callback_data=f'order_num_{order.code}'))
    
    return keyboard.adjust(1).as_markup()

async def order_take(code):

    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Замовлення забрали ✅', callback_data=f'order_take_{code}'))
    keyboard.add(InlineKeyboardButton(text='Скасувати ❌', callback_data='back_to_order_num'))
    
    return keyboard.adjust(1).as_markup()

async def agree(code):
    
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Згоден ✅', callback_data=f'agree_{code}'))
    
    return keyboard.adjust(1).as_markup()

async def generate_date_buttons():
    
    today = datetime.now().date()
    
    # Назви днів тижня
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт"]
    
    buttons = []
    added_days = 0
    delta = 0
    
    
    # Генеруємо кнопки для сьогодні + 5 робочих днів
    while added_days < 6:
        current_date = today + timedelta(days=delta)
        if current_date.weekday() < 5:  # Тільки будні
            date_str = current_date.strftime("%d.%m.%Y")
            callback_data = f"date_{current_date.strftime('%Y-%m-%d')}"
            
            msg = f"{date_str.split('.')[0]}.{date_str.split('.')[1]}"
            
            if delta == 0:
                buttons.append(InlineKeyboardButton(
                    text=f"Сьогодні ({msg})", 
                    callback_data=callback_data
                ))
            else:
                day_name = weekdays[current_date.weekday()]
                buttons.append(InlineKeyboardButton(
                    text=f"{day_name} {msg}", 
                    callback_data=callback_data
                ))
            added_days += 1
        delta += 1
    
    # Правильне створення InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        buttons[i:i+3] for i in range(0, len(buttons), 3)
    ])
    
    return keyboard