from fastapi import HTTPException
from app.auth import auth


async def services_add_user(hashed_password: str):
    return await auth.hash_password(hashed_password)


async def services_cheak_user_id(user1, user2):
    if user1 == user2:
        raise HTTPException(status_code=400, detail="You entered yourself, please enter another user.")


async def services_cheak_chat_id(chat_id, db: AsyncSession):
    chat_stmt = select(models.Chat).where(models.Chat.id == chat_id)
    chat_result = await db.execute(chat_stmt)
    chat = chat_result.scalars().first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
