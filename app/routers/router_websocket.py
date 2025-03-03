import logging
from datetime import datetime

from fastapi import WebSocket, Query, HTTPException, Depends, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.auth import get_current_user
from app.crud.crud import create_message
from app.database.database import get_db
from app.models.models import Message, ChatUser, group_members, Chat

user_router_websocket = APIRouter(tags=["ws"])

logging.basicConfig(filename='app.log',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def broadcast(self, message: str, sender_id: str):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            if client_id != sender_id:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logging.error(f"Failed to send to {client_id}: {e}")
                    disconnected_clients.append(client_id)
        for client_id in disconnected_clients:
            await self.disconnect(client_id)


manager = ConnectionManager()


@user_router_websocket.websocket("/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str = Query(...),
                             db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    current_user = await authenticate_user(websocket, db, token)
    if current_user is None:
        await websocket.close()
        return
    if not await check_access(db, chat_id, current_user):
        await websocket.close()
        return
    await manager.connect(websocket, current_user.username)
    await send_unread_messages(websocket, db, chat_id)
    await handle_websocket_communication(websocket, db, chat_id, current_user)


async def authenticate_user(websocket: WebSocket, db: AsyncSession, token: str):
    try:
        current_user = await get_current_user(db, token)
        logging.info(f"Authenticated user: {current_user.username}")
        return current_user
    except HTTPException as e:
        logging.warning(f"Authentication failed: {e.detail}")
        await websocket.close()
        return None
    except Exception as e:
        logging.error(f"An error occurred during authentication: {e}")
        await websocket.close()
        return None


async def check_access(db: AsyncSession, chat_id: int, current_user):
    chat = await db.execute(select(Chat).where(Chat.id == chat_id))  
    chat_record = chat.scalar()

    if chat_record is None:
        logging.warning(f"Chat {chat_id} does not exist.")
        return False

    if chat_record.type == "group":
        group_members_query = await db.execute(
            select(group_members)
            .where(
                group_members.c.group_id == chat_id,
                group_members.c.user_id == current_user.id
            )
        )
        if group_members_query.scalar() is None:
            logging.warning(f"Access denied for user {current_user.id} to group chat {chat_id}")
            return False
    else:
        chat_users = await db.execute(select(ChatUser).where(ChatUser.chat_id == chat_id))
        chat_user_ids = [chat_user.user_id for chat_user in chat_users.scalars().all()]

        if current_user.id not in chat_user_ids:
            logging.warning(f"Access denied for user {current_user.id} to private chat {chat_id}")
            return False

    return True


async def send_unread_messages(websocket: WebSocket, db: AsyncSession, chat_id: int):
    unread_messages = await db.execute(select(Message).where(Message.chat_id == chat_id, Message.read == False))
    for message in unread_messages.scalars().all():
        await websocket.send_text(f"Client #{message.sender_id} says: {message.text}")
        message.read = True
    await db.commit()


async def handle_websocket_communication(websocket: WebSocket, db: AsyncSession, chat_id: int, current_user):
    last_timestamp = None
    try:
        while True:
            data = await websocket.receive_text()
            current_timestamp = datetime.now()

            if last_timestamp and (current_timestamp - last_timestamp).total_seconds() < 1:
                logging.warning(f"Duplicate message detected from {current_user.username}. Ignoring.")
                continue

            await process_message(chat_id, current_user, data, db)
            await broadcast_message(current_user.username, data)

            last_timestamp = current_timestamp

    except Exception as e:
        logging.error(f"An error occurred during the WebSocket communication: {e}")
    finally:
        await disconnect_user(current_user.username)


async def process_message(chat_id: int, current_user, text: str, db: AsyncSession):
    await create_message(chat_id, current_user, text, db)
    logging.info(f"Received message from {current_user.username}: {text}")


async def broadcast_message(sender_username: str, message: str):
    await manager.broadcast(f"Client #{sender_username} says: {message}", sender_username)


async def disconnect_user(username: str):
    await manager.disconnect(username)
    logging.info(f"User {username} disconnected")
