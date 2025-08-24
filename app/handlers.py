from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from collections import defaultdict
import asyncio
from datetime import datetime
import config
import os
import app.keyboards as kb
import app.database.requests as rq

router = Router()

user_messages = defaultdict(list)

class MakeOrder(StatesGroup):
    item_id_name = State()
    date = State()
    shift = State()
    interval = State()

class ChangeStates(StatesGroup):
    item_id = State()
    count = State()

class AdminStates(StatesGroup):
    waiting_for_admin_id = State()

# user com

async def delete_previous_messages(user_id: int, chat_id: int, bot):
    if user_id in user_messages:
        for msg_id in user_messages[user_id]:
            try:
                await bot.delete_message(chat_id, msg_id)
            except:
                pass
        del user_messages[user_id]

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Вітаю! Оберіть ліцей у якому навчаєтесь ви чи ваша дитина 👇🏻', reply_markup=await kb.lyceums())

@router.callback_query(F.data.startswith('lyceum_'))
async def lyceum_ans(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await rq.set_user(callback.from_user.id, callback.data.split("_")[1])
    await callback.answer('Ви успішно обрали свій ліцей!')
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    await callback.message.answer(f'<b>Ви обрали - Вараський ліцей №{callback.data.split("_")[1]}!</b> 🏫', parse_mode='HTML')
    await asyncio.sleep(0.5)
    await callback.message.answer('<i>Тепер ви можете зробити замовлення й посмакувати смачною випічкою та смачними напоями! 🥰</i>', parse_mode='HTML')
    await asyncio.sleep(0.5)
    await callback.message.answer('''<b>Яким чином відбувається отримання продукту?</b>\n
1. Ви обираєте на якій перерві та в який день ви хочете забрати продукт з буфету.\n 
2. Після оплати бот надає згенерований номер, який ви повинні сказати продавчині.\n
3. Ви отримуєте свій продукт.''', reply_markup=kb.main, parse_mode='HTML')
    
@router.message(F.text == 'Обрати інший ліцей')
async def ch_lyceum(message: Message):
    await message.answer('Оберіть ліцей на котрий бажаєте змінити!', reply_markup=await kb.lyceums())

@router.message(F.text == 'Зв`язок з адміністрацією')
async def cm_admin(message: Message):
    await message.answer('Ви можете написати нам в Телеграм, якщо виникли технічні неполадки, або є запитання: @nzor0')
    
@router.message(F.text == 'Зробити замовлення')
async def mk_order(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await rq.change_actual_by_user_id(user_id)
    await delete_previous_messages(user_id, chat_id, message.bot)
    
    await message.answer('Ваша 🛒 корзина порожня! Швидше наповни її!')
    msg = await message.answer('<b>Що ви бажаєте обрати першим?</b>', reply_markup=await kb.categories(), parse_mode='HTML')
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data == 'add_to_cart_category')
async def add_to_cart_category(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await callback.answer()
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    msg = await callback.message.answer(
        '<b>Що ви бажаєте додати до корзини?</b>', 
        reply_markup=await kb.categories(), 
        parse_mode='HTML'
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)
    
@router.callback_query(F.data == 'to_main')
async def to_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await asyncio.sleep(1)
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    await callback.answer('Ви потрапили в головне меню')
    await callback.message.answer('<b>Ви потрапили в головне меню.</b>', reply_markup=kb.main, parse_mode='HTML')

@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await asyncio.sleep(1)
    await delete_previous_messages(user_id, chat_id, callback.bot)

    category_data = await rq.get_category_name(callback.data.split("_")[1])
    items = await rq.get_category_item(category_data.id, user_id)
    await callback.answer(f'Ви обрали категорію {(category_data.name).lower()}')

    user_messages[user_id] = []
    for item in items:
        await asyncio.sleep(0.05)
        msg = await callback.message.answer(
            f'<b>{item.name}</b> - ({item.price} грн.)',
            parse_mode='HTML',
            reply_markup=await kb.more_info(item.id)
        )
        user_messages[user_id].append(msg.message_id)

    await asyncio.sleep(0.3)
    msg = await callback.message.answer(
        f'Перед вами всі товари категорії {(category_data.name).lower()}.\n'
        'Щоб додати товар до кошика, натисніть <i>більше інформації</i> на обраному продукті!',
        parse_mode='HTML'
    )
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('more_info_'))
async def item(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await asyncio.sleep(1)
    await delete_previous_messages(user_id, chat_id, callback.bot)

    item_data = await rq.get_item(callback.data.split("_")[2])
    await callback.answer(f'Ви обрали товар: {(item_data.name).lower()}')

    file_path = os.path.join("photo", f"{item_data.photo}.jpg")
    photo_msg = await callback.message.answer_photo(
        photo=FSInputFile(path=file_path, filename=item_data.photo),
        caption=(
            f'Назва товару: {(item_data.name).lower()}\n'
            f'Опис товару: {(item_data.description).lower()}\n' 
            f'Ціна товару: {item_data.price} ₴\n'
            f'Кількість товару на <b>сьогодні</b>: {item_data.count} шт.\n\n'
            f'<i>P.S: Якщо замовляєте на потім, кількість - не грає ролі</i>😉'
        ),
        parse_mode='HTML',
        reply_markup=await kb.item_data(item_data.id)
    )
    
    user_messages[user_id] = [photo_msg.message_id]

@router.callback_query(F.data.startswith('add_item_'))
async def add_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    item_data = await rq.get_item(callback.data.split("_")[2])
    await callback.answer(f'Ви обрали товар: {(item_data.name).lower()}')
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    msg = await callback.message.answer('Оберіть кількість:', reply_markup=await kb.count(item_data.id))
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('add_to_cart_item_'))
async def add_to_cart_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    item_data = await rq.get_item(callback.data.split("_")[4])
    await rq.add_to_cart(callback.from_user.id, item_data.id, callback.data.split("_")[5])
    await callback.answer(f'Ви успішно додали товар: {item_data.name}\n у кількості: {callback.data.split("_")[5]} шт.')
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    order = await rq.get_order(user_id)
    info = order.catalog.split('_')
    message = ''
    
    for i in range(0, len(info), 2):
        item_name = info[i]
        item_count = info[i + 1]
        message += f'{item_name}: {item_count} шт.\n'
    
    msg = await callback.message.answer(
        f"<b>Ваша корзина:</b>\n\n{message}\nВи можете продовжити вибір товарів, або ж оплатити товари в кошику!",
        reply_markup=await kb.req_shop(user_id),
        parse_mode='HTML'
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('cart_buy'))
async def buy_cart_item(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    item_data = await rq.get_item(callback.data.split("_")[2])
    await callback.answer()
    await state.update_data(item_id_name=item_data.id)
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    msg = await callback.message.answer(
        '<i>Оберіть дату, коли ви маєте отримати замовлення</i>', 
        reply_markup=await kb.generate_date_buttons(),
        parse_mode='HTML'
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('date_'))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    date_str = callback.data.split('_')[1]
    try:
        valid_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if valid_date < today:
            await callback.answer('❌ Не можна обрати минулу дату!', show_alert=True)
            return
        
        formatted_date = valid_date.strftime("%d.%m.%Y")
        await callback.message.edit_text(
            f'📅 Обрана дата: <b>{formatted_date}</b>\nТепер оберіть зміну:',
            parse_mode='HTML'
        )
        
        await state.update_data(date=formatted_date)
        await state.set_state(MakeOrder.shift)
        
        await delete_previous_messages(user_id, chat_id, callback.bot)
        msg = await callback.message.answer(
            '🕒 Оберіть бажану зміну:',
            reply_markup=kb.shifts
        )
        
        if user_id not in user_messages:
            user_messages[user_id] = []
        user_messages[user_id].append(msg.message_id)

    except Exception:
        await callback.answer('❌ Помилка при обробці дати', show_alert=True)

@router.callback_query(F.data.startswith('shifts_'))
async def give_shift(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await callback.answer('Ви успішно обрали зміну!')
    await state.update_data(shift=callback.data.split("_")[1])
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    msg = await callback.message.answer(
        'Оберіть перерву для отримання замовлення!', 
        parse_mode='HTML', 
        reply_markup=await kb.intervals(callback.data.split("_")[1])
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('interval_'))
async def give_break(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await callback.answer('Ви успішно обрали перерву!')
    await state.update_data(interval=callback.data.split("_")[2])
    data = await state.get_data()
    await rq.add_order_data(callback.from_user.id, f'{data["date"]}_{data["shift"]}_{data["interval"]}')
    
    order = await rq.get_order(callback.from_user.id)
    info = order.catalog.split('_')

    date_str = data['date']
    valid_date = datetime.strptime(date_str, "%d.%m.%Y").date()
    today = datetime.now().date()

    message = ''
    out_of_stock_items = []

    if today == valid_date:
        for i in range(0, len(info) - 1, 2):
            item_name = info[i]
            item_count = int(info[i + 1])
            item_info = await rq.get_item_by_name(item_name, order.lyceum)
            
            if item_info.count < item_count:
                out_of_stock_items.append(f'{item_name}: {item_count} шт.')
            else:
                message += f'{item_name}: {item_count} шт.\n'

        if out_of_stock_items:
            out_of_stock_message = '\n'.join(out_of_stock_items)
            await delete_previous_messages(user_id, chat_id, callback.bot)
            msg = await callback.message.answer(
                f'❌ <b>На жаль, наступні товари не доступні в потрібній кількості:</b>\n{out_of_stock_message}\n'
                'Будь ласка, оберіть інший варіант. Приносимо вибачення!',
                parse_mode='HTML', reply_markup=kb.main
            )
            user_messages[user_id].append(msg.message_id)
            await rq.change_actual(order.id)
            return

    else:
        for i in range(0, len(info), 2):
            item_name = info[i]
            item_count = info[i + 1]
            message += f'{item_name}: {item_count} шт.\n'

    await delete_previous_messages(user_id, chat_id, callback.bot)
    msg = await callback.message.answer(
        f'''<b>Ваше замовлення готове!✅</b>\n{message}Забрати замовлення: <b>{data['date']}, {data['shift']} зміна, {data['interval']} перерва</b>\nДо сплати: <b>{order.price} грн.</b>\nВараський ліцей №{order.lyceum}''',
        parse_mode='HTML',
        reply_markup=await kb.buy(order.id)
    )
    user_messages[user_id].append(msg.message_id)

@router.callback_query(F.data.startswith('delete_cart_'))
async def delete_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await delete_previous_messages(user_id, chat_id, callback.bot)
    await callback.answer('')
    await callback.message.answer('🛒 Корзину успішно очищено!', reply_markup=kb.main)
    await rq.change_actual(callback.data.split("_")[-1])

@router.callback_query(F.data.startswith('buy_'))
async def agree(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await callback.answer('')
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    msg1 = await callback.message.answer(
        '''Натискаючи кнопку <b>\"Згоден\"</b> ви погоджуєтесь з Договором оферти та Політикою конфіденційності телеграм-боту, та зможете оплатити ваше замовлення''',
        reply_markup=await kb.agree(callback.data.split("_")[1]),
        parse_mode='HTML'
    )
    msg2 = await callback.message.answer(
        '<i>P.S. "Інше"</i> ⬇️', 
        reply_markup=kb.main,
        parse_mode='HTML'
    )
    
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].extend([msg1.message_id, msg2.message_id])

@router.callback_query(F.data.startswith('agree_'))
async def buy_cart(callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    await callback.answer('')
    await delete_previous_messages(user_id, chat_id, callback.bot)
    
    order = await rq.get_order(callback.from_user.id)
    info = order.catalog.split('_')
    prices = []
    
    for i in range(0, len(info) - 1, 2):
        price = await rq.get_price_by_name(info[i])
        amount = int(price * int(info[i + 1])) * 100
        prices.append(LabeledPrice(label=f"{info[i]}: {info[i + 1]} шт.", amount=amount))

    try:
        await callback.message.answer_invoice(
            title='Оплата замовлення!',
            description='Натисніть нижче, щоб оплатити замовлення!',
            payload=f"order_{callback.from_user.id}",
            provider_token=config.PAYMENT_TOKEN,
            currency='UAH',
            prices=prices,
            start_parameter='create_invoice',
            need_shipping_address=False,
            is_flexible=False
        )
    except TelegramBadRequest as e:
        msg = await callback.message.answer(f"Помилка при створенні рахунку: {e.message}")
        user_messages[user_id].append(msg.message_id)

@router.pre_checkout_query()
async def checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.content_type == "successful_payment")
async def successful_payment(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    await delete_previous_messages(user_id, chat_id, message.bot)
    
    order = await rq.get_order(user_id)
    await message.answer(
        f'✅ <b>Оплата успішна!</b>\n📦 Номер замовлення: <code>{order.code}</code>\n'
        f'🚚 Заберіть: {order.date.split("_")[0]}, {order.date.split("_")[1]} зміна, {order.date.split("_")[2]} перерва',
        parse_mode='HTML',
        reply_markup=kb.main
    )
    
    today = datetime.now().strftime("%d.%m.%Y")
    if order.date.split("_")[0] == today:
        await rq.change_order_pay(order.id)
        catalog_items = order.catalog.split('_')
        for i in range(0, len(catalog_items), 2):
            if i + 1 < len(catalog_items):
                item_name = catalog_items[i]
                item_count = catalog_items[i+1]
                await rq.change_count_product(item_name, item_count, order.lyceum)

@router.message(F.text == 'Інше')
async def dodatok(message: Message):
    doc1 = FSInputFile(os.path.join("docs", "ПУБЛІЧНИЙ_ДОГОВІР_ОФЕРТА_НА_ПРОДАЖ_ХАРЧОВИХ_ПРОДУКТІВ.pdf"))
    doc2 = FSInputFile(os.path.join("docs", "ПОЛІТИКА_КОНФІНДЕНЦІЙНОСТІ.pdf"))
    doc3 = FSInputFile(os.path.join("docs", "КОНТАКТНА_ІНФОРМАЦІЯ.pdf"))
    
    await message.answer_document(doc1)
    await message.answer_document(doc2)
    await message.answer_document(doc3)

#admin com

@router.message(Command('admin'))
async def admin_panel(message: Message):
    user = await rq.get_user(message.from_user.id)
    
    if user:
        await message.answer('Вітаю, оберіть ліцей у якому хочете змітини наявність продуктів або видати замовлення!', reply_markup=await kb.admin_lyceums())
    
    else:
        await message.answer('У вас немає прав адміністратора, якщо вони мають бути у вас зверніться до іншого адміністратора!')

@router.callback_query(F.data.startswith('admin_lyceum_'))
async def admin_menu(callback: CallbackQuery):
    await rq.set_lyceum(callback.from_user.id, callback.data.split("_")[2])
    await callback.answer('Ви успішно обрали ліцей!')
    await callback.message.answer('Оберіть дію в меню!', reply_markup= kb.admin)

@router.message(F.text == 'Активні замовлення')
async def active_order_1(message: Message):
    user = await rq.check_admin(message.from_user.id)
    if user:
        user = await rq.get_user(message.from_user.id)
        await message.answer(f'Оберіть замовлення з Вараського ліцею №{user.lyceum} нижче!', reply_markup= await kb.all_order(user.lyceum))
    else:
        await message.answer('У вас немає прав для цього!')

@router.callback_query(F.data.startswith('back_to_order_num'))
async def active_order_2(callback: CallbackQuery):
    
    await callback.message.delete()
    callback.answer('')
    
    user = await rq.check_admin(callback.from_user.id)
    
    if user:
        user = await rq.get_user(callback.from_user.id)
        await callback.message.answer(f'Оберіть замовлення з Вараського ліцею №{user.lyceum} нижче!', reply_markup= await kb.all_order(user.lyceum))
    else:
        await callback.message.answer('У вас немає прав для цього!')
    

@router.callback_query(F.data.startswith('order_num_'))
async def take_order(callback: CallbackQuery):
    order = await rq.get_order_by_code(callback.data.split("_")[2])
    
    await callback.message.delete()
    
    await callback.answer(f'Ви обрали замовлення №{order.code}!')
    
    info = order.catalog.split('_')
    message = ''
    while info:
        item_name = info.pop(0)
        item_count = info.pop(0)
        message += f'{item_name}: {item_count} шт.\n'
    
    await callback.message.answer(f'''Замовлення №{order.code}\n\n{message}\nЗамовлення заберуть: {order.date.split("_")[0]}, {order.date.split("_")[1]} зміна, {order.date.split("_")[2]} перерва!''', 
                                  reply_markup= await kb.order_take(order.code))
    
@router.callback_query(F.data.startswith('order_take_'))
async def order_taken(callback: CallbackQuery):
    order = await rq.get_order_by_code(callback.data.split("_")[2])
    
    user = await rq.get_user(callback.from_user.id)
    
    await callback.message.delete()
    
    await callback.answer(f'Замовлення №{order.code} успішно видано!')
    await callback.message.answer(f'Замовлення №{order.code} видано!')
    
    await rq.change_actual(order.id)
    
    await callback.message.answer(f'Оберіть замовлення з Вараського ліцею №{user.lyceum} нижче!', reply_markup= await kb.all_order(user.lyceum))
    

@router.message(F.text == 'Змінити наявність')
async def set_new_count_category(message: Message):
    user = await rq.check_admin(message.from_user.id)
    
    if user:
        await message.answer('Оберіть категорію, де хочете змінювати кількість товару', 
                             reply_markup=await kb.admin_categories())
    
    else:
        await message.answer('У вас немає прав для цього!')
        
@router.callback_query(F.data.startswith('admin_to_main_'))
async def admin_to_main(callback:CallbackQuery):
    user = await rq.check_admin(callback.from_user.id)
    
    await callback.message.delete()
    
    callback.answer(' ')
    
    if user:
        await callback.message.answer('Оберіть категорію, де хочете змінювати кількість товару', 
                             reply_markup=await kb.admin_categories())
    
    else:
        await callback.message.answer('У вас немає прав для цього!')

    
@router.callback_query(F.data.startswith('admin_category_'))
async def set_new_count_items(callback: CallbackQuery):
    await callback.message.delete()
    
    await callback.answer('Ви успішно обрали категорію!')
    await callback.message.answer('Оберіть продукт, на якому хочете змінити кількість товару', 
                                  reply_markup=await kb.admin_items(callback.data.split("_")[2], callback.from_user.id,))
    
@router.callback_query(F.data.startswith('admin_items_'))
async def set_new_count_item(callback: CallbackQuery, state:FSMContext):
    
    item = await rq.get_item(callback.data.split("_")[2])
    
    await callback.answer('Ви успішно обрали товар!')
    await callback.message.answer(f'Введіть нову кількість для товару {(item.name).lower()}')
    
    await state.update_data(item_id = item.id)
    await state.set_state(ChangeStates.count)

@router.message(ChangeStates.count)
async def change_count(message: Message, state:FSMContext):
    
    await message.delete()
    
    await state.update_data(count = int(message.text))    
    
    data = await state.get_data()
    
    await rq.change_count(data['item_id'], data['count'])
    
    item = await rq.get_item(data['item_id'])
    
    await message.answer(f'Ви успішно змінили кількість товару {(item.name).lower()} на {item.count} шт.')
    
    await state.clear()

@router.message(Command('set_admin'))
async def set_admin(message: Message, state:FSMContext):
    user = await rq.get_user(message.from_user.id)
    if user:
        await message.answer('''Введіть telegram id користувача, якого ви хочете зробити адміністратором.\n\n<i>Щоб дізнатись telegram id, перейдіть в бот @username_to_id_bot -> User -> потрібний користувач -> User id</i>''',
                             parse_mode='HTML')
        await state.set_state(AdminStates.waiting_for_admin_id.state)
    else:
        await message.answer('У вас немає прав адміністратора, якщо вони у вас мають бути зверніться до іншого адміністратора!')

@router.message(AdminStates.waiting_for_admin_id)
async def set_admin_id(message: Message, state:FSMContext):
    try:
        new_admin_id = int(message.text)
        if len(message.text) < 9:
            await message.answer('Введений ID виглядає некоректно. Будь ласка, перевірте ще раз.')
            return

        await rq.set_admin(new_admin_id)
        await message.answer(f'Користувач з ID {new_admin_id} успішно зроблений адміністратором!')
    
    except ValueError:
        
        await message.answer('Будь ласка, введіть коректний числовий ID.')
    
    await state.clear()