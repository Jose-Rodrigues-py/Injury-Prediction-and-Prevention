from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

DATABASE_URL = "postgresql+asyncpg://postgres:devpass@localhost:5432/athletelog"

engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True prints SQL — great for learning, turn off later

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session