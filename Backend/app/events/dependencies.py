from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.events.repositories import EventRepository
from app.events.services import EventService


async def get_event_service(session: AsyncSession = Depends(get_session)) -> EventService:
    repository = EventRepository(session)
    return EventService(repository)
