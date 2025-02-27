from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.auth import auth
from app.auth.auth import authenticate_user, create_access_token
from app.crud import crud
from app.crud.crud import create_chat_crud, create_chat_group
from app.database.database import get_db
from app.models import models
from app.schemas import schemas

user_router_user = APIRouter()


@user_router_user.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user(db, user)


@user_router_user.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username.lower(), form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = await create_access_token(data={"sub": user.username})
    return {"token_type": "bearer", "access_token": access_token}


@user_router_user.post("/add-chat-privat", response_model=schemas.Chat)
async def add_chat(chat: schemas.ChatCreate, user_2_id: int, db: AsyncSession = Depends(get_db),
                   user: models.User = Depends(auth.get_current_user)):
    return await create_chat_crud(chat, user.id, user_2_id, db)


@user_router_user.post("/add-chat-group", response_model=schemas.Group)
async def add_chat_group(group_chat: schemas.GroupCreate, db: AsyncSession = Depends(get_db),
                         user: models.User = Depends(auth.get_current_user)):
    return await create_chat_group(group_chat, db)


@user_router_user.get("/history", response_model=schemas.MessageResponce)
async def get_history(chat_id: int,
                      db: AsyncSession = Depends(get_db),
                      user: models.User = Depends(auth.get_current_user),
                      limit: int = Query(10, gt=0),offset: int = Query(0, ge=0)):
    messages = await crud_get_history(db, limit, chat_id, offset)
    response = schemas.MessageResponce(text=[message.text for message in messages])
    return response
