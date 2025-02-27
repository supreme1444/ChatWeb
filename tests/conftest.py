from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.crud.crud import create_user, create_chat_crud, create_message, create_chat_group
from app.models import models
from app.models.models import User
from app.schemas import schemas
from app.schemas.schemas import UserCreate

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Создаёт тестовую БД перед тестами и удаляет после."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Создаёт новую сессию БД для каждого теста."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user_data = UserCreate(username="testuser", email="test@example.com", password="testpassword")
    user = await create_user(db_session, user_data)
    await db_session.commit()
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    user_from_db = await db_session.get(User, user.id)
    assert user_from_db is not None
    assert user_from_db.username == "testuser"
    assert user_from_db.email == "test@example.com"


@pytest.mark.asyncio
async def test_create_chat_crud(db_session: AsyncSession):
    chat_data = schemas.ChatCreate(name="Private Chat")
    user_1_id = 1
    user_2_id = 2

    chat = await create_chat_crud(chat_data, user_1_id, user_2_id, db_session)

    assert chat.id is not None
    assert chat.name == "Private Chat"
    assert chat.type == "privat"

    chat_users = await db_session.execute(
        models.ChatUser.__table__.select().where(models.ChatUser.chat_id == chat.id)
    )
    chat_users = chat_users.fetchall()
    assert len(chat_users) == 2
    assert chat_users[0].user_id == user_1_id
    assert chat_users[1].user_id == user_2_id


@pytest.mark.asyncio
async def test_create_message(db_session: AsyncSession):
    chat_id = 1
    current_user = models.User(id=1, username="testuser", email="test@example.com")
    text = "Hello, world!"
    message = await create_message(chat_id, current_user, text, db_session)
    assert message.id is not None
    assert message.chat_id == chat_id
    assert message.sender_id == current_user.id
    assert message.text == text
    assert isinstance(message.timestamp, datetime)
    assert message.read is False


@pytest.mark.asyncio
async def test_create_chat_group(db_session: AsyncSession):
    group_chat_data = schemas.GroupCreate(
        name="Group_Chat",
        creator_id=1,
        members=[1, 2, 3]
    )
    group = await create_chat_group(group_chat_data, db_session)
    assert group.id is not None
    assert group.name == "Group_Chat"
    assert group.creator_id == 1
    assert group.members == [1, 2, 3]

    chat = await db_session.get(models.Chat, group.id)
    assert chat is not None
    assert chat.name == "Group_Chat"
    assert chat.type == "group"
    group_members = await db_session.execute(
        models.group_members.select().where(models.group_members.c.group_id == group.id)
    )
    group_members = group_members.fetchall()
    assert len(group_members) == 3
    assert group_members[0].user_id == 1
    assert group_members[1].user_id == 2
    assert group_members[2].user_id == 3
