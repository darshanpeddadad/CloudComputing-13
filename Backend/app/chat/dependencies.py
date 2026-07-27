from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.chat.services import ChatService


async def get_chat_service(session: AsyncSession = Depends(get_session)) -> ChatService:
    return ChatService(session)
