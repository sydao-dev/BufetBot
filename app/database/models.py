from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    is_admin: Mapped[bool] = mapped_column(default=False)
    lyceum: Mapped[int] = mapped_column(ForeignKey('lyceums.id'))
    
class Category(Base):
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(10))
    
class Item(Base):
    __tablename__ = 'items'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(120))
    price: Mapped[int] = mapped_column()
    count: Mapped[int] = mapped_column()
    category: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    lyceum: Mapped[int] = mapped_column(ForeignKey('lyceums.id'))
    photo: Mapped[str] = mapped_column(String(100))
    
class Lyceum(Base):
    __tablename__ = 'lyceums'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(10))
    number: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=False)
    
class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[int] = mapped_column()
    catalog: Mapped[str] = mapped_column(String(200))
    is_actual: Mapped[bool] = mapped_column(default=True)
    is_pay: Mapped[bool] = mapped_column(default=False)
    code: Mapped[str] = mapped_column()
    lyceum: Mapped[int] = mapped_column(ForeignKey('lyceums.id'))
    user = mapped_column(BigInteger, ForeignKey('users.tg_id'))
    date: Mapped[str] = mapped_column(String(200), default='')
    
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)