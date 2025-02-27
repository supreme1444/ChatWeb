from fastapi import HTTPException
from app.auth import auth


async def services_add_user(hashed_password: str):
    return await auth.hash_password(hashed_password)


async def services_cheak_user_id(user1, user2):
    if user1 == user2:
        raise HTTPException(status_code=400, detail="You entered yourself, please enter another user.")
