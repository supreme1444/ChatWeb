from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import models
from app.schemas import schemas
from app.services.services import services_add_user, services_cheak_user_id


async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = await services_add_user(user.password)
    db_user = models.User(username=user.username.lower(), email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_chat_crud(chat: schemas.ChatCreate, user_1_id: int, user_2_id: int, db: AsyncSession):
    await services_cheak_user_id(user_1_id, user_2_id)
    db_chat_create = models.Chat(name=chat.name, type="privat")
    db.add(db_chat_create)
    await db.commit()
    await db.refresh(db_chat_create)
    db_chat_user_1 = models.ChatUser(chat_id=db_chat_create.id, user_id=user_1_id)
    db_chat_user_2 = models.ChatUser(chat_id=db_chat_create.id, user_id=user_2_id)
    db.add(db_chat_user_1)
    db.add(db_chat_user_2)
    await db.commit()

    return db_chat_create


async def create_message(chat_id: int, current_user, text: str, db: AsyncSession):
    new_message = models.Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        text=text,
        timestamp=datetime.now(),
        read=False
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message


async def create_chat_group(group_chat: schemas.GroupCreate, db: AsyncSession):
    new_chat = models.Chat(
        name=group_chat.name,
        type="group"
    )
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    new_group = models.Group(
        name=group_chat.name,
        creator_id=group_chat.creator_id
    )
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    for member_id in group_chat.members:
        await db.execute(models.group_members.insert().values(user_id=member_id, group_id=new_group.id))
    await db.commit()
    return schemas.Group(
        id=new_group.id,
        name=new_group.name,
        creator_id=new_group.creator_id,
        members=group_chat.members
    )


async def crud_get_history(db: AsyncSession, limit, chat_id: int, offset: int,):
    await services_cheak_chat_id(chat_id,db)
    output = (
        select(models.Message)
        .where(models.Message.chat_id == chat_id)
        .order_by(asc(models.Message.timestamp))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(output)
    history_items = result.scalars().all()
    return history_items
