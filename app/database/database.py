import os

from databases import Database
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
db = Database(DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def connect():
    await db.connect()


async def disconnect():
    await db.disconnect()
