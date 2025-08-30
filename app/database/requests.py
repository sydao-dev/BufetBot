from app.random_code import generate_code
from app.database.models import async_session
from app.database.models import User, Category, Item, Lyceum, Order
from sqlalchemy import select

async def set_user(tg_id, lyceum):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if user: 
            if user.lyceum != lyceum:
                user.lyceum = lyceum
                await session.commit()
        else:
            new_user = User(tg_id = tg_id, lyceum = lyceum)
            session.add(new_user)
            await session.commit()

async def get_categories():
    async with async_session() as session:
        return await session.scalars(select(Category))

async def get_category_name(category_id):
    async with async_session() as session:
        return await session.scalar(select(Category).where(Category.id == category_id))
    
async def get_category_item(category_id, tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return await session.scalars(select(Item).where((Item.category == category_id) & (Item.lyceum == user.lyceum)))
    
async def get_item(item_id):
    async with async_session() as session:
        return await session.scalar(select(Item).where(Item.id == item_id))
    
async def get_lyceums():
    async with async_session() as session:
        return await session.scalars(select(Lyceum).where(Lyceum.is_active == True))
    
async def add_to_cart(tg_id, item, count):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.user == tg_id) & (Order.is_pay == False) & (Order.is_actual == True)))
        item  = await session.scalar(select(Item).where(Item.id == item))
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if order:
            order.catalog += f'_{item.name}_{count}'
            order.price += item.price * int(count)
            await session.commit()
        
        if not order:
            code = generate_code()
            order = await session.scalar(select(Order).where((Order.code == code) & (Order.is_actual == True)))
            
            while order:
                code = generate_code()
                order = await session.scalar(select(Order).where((Order.code == code) & (Order.is_actual == True)))   
            
            new_order = Order(price = item.price * int(count), catalog = f'{item.name}_{count}', code = code, lyceum = user.lyceum, user = user.tg_id)
            session.add(new_order)
            await session.commit()
            
async def get_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where((User.tg_id == tg_id) & (User.is_admin == True)))
        return user

async def set_lyceum(tg_id, lyceum):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            if user.lyceum != lyceum:
                user.lyceum = lyceum
                await session.commit()

async def set_admin(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.is_admin = True
            await session.commit()
        else:
            new_user = User(tg_id = tg_id, lyceum = 1, is_admin = True)
            session.add(new_user)
            await session.commit()

async def change_count(item_id, new_count):
    async with async_session() as session:
        item = await session.scalar(select(Item).where(Item.id == item_id))
        item.count = new_count
        await session.commit()
        
async def get_order(tg_id):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.user == tg_id) & (Order.is_pay == False) & (Order.is_actual == True)))
        return order
    
async def get_orders(lyceum):
    async with async_session() as session:
        orders = await session.scalars(select(Order).where((Order.lyceum == lyceum) & (Order.is_pay == True) & (Order.is_actual == True)))
        return orders.all()
    
async def get_price_by_name(item_name):
    async with async_session() as session:
        item = await session.scalars(select(Item).where(Item.name == item_name))
        item = item.first()
        return int(item.price) if item else None
    
async def add_order_data(tg_id, date):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.user == tg_id) & (Order.is_pay == False) & (Order.is_actual == True)))
        order.date = date
        await session.commit()
        
async def change_order_pay(id):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.id == id) & (Order.is_pay == False)))
        order.is_pay = True
        await session.commit()
        
async def get_order_by_code(code):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.code == code) & (Order.is_pay == True) & (Order.is_actual == True)))
        return order
    
async def change_actual(id):
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == id))
        order.is_actual = False
        await session.commit()
        
async def change_actual_by_user_id(user_id):
    async with async_session() as session:
        order = await session.scalar(select(Order).where((Order.user == user_id) & (Order.is_pay == False) & (Order.is_actual == True)))
        if order:
            order.is_actual = False
        await session.commit()

async def check_admin(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where((User.tg_id == tg_id) & (User.is_admin == True)))
        return user
    
async def get_item_by_name(name, lyceum):
    async with async_session() as session:
        item = await session.scalar(select(Item).where((Item.name == name) & (Item.lyceum == lyceum)))
        return item
    
async def change_count_product(item_name, item_count, lyceum):
    async with async_session() as session:
        item = await session.scalar(select(Item).where((Item.name == item_name) & (Item.lyceum == lyceum)))
        item.count -= int(item_count)
        await session.commit()
        
async def get_admin(lyceum):
    async with async_session() as session:
        admins = await session.scalars(
            select(User).where(
                (User.lyceum == lyceum) & 
                (User.is_admin == True)
            )
        )
        return admins.all()