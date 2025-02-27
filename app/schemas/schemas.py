from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    name: str


class Chat(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


class Message(BaseModel):
    chat_id: int
    sender_id: int
    text: str
    timestamp: datetime
    read: bool


class GroupCreate(BaseModel):
    name: str
    creator_id: int
    members: List[int]


class Group(BaseModel):
    id: int
    name: str
    creator_id: int
    members: List[int]

    class Config:
        from_attributes = True


class MessageResponce(BaseModel):
    text: List

