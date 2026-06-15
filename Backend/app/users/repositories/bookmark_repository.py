from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.users.models.event_bookmark import EventBookmark
from app.events.models.event import Event

class BookmarkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, event_id: str) -> EventBookmark:
        bookmark = EventBookmark(user_id=user_id, event_id=event_id)
        self.session.add(bookmark)
        await self.session.commit()
        await self.session.refresh(bookmark)
        return bookmark

    async def delete(self, user_id: str, event_id: str) -> bool:
        query = delete(EventBookmark).where(
            and_(EventBookmark.user_id == user_id, EventBookmark.event_id == event_id)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def get_all_by_user(self, user_id: str) -> List[EventBookmark]:
        query = select(EventBookmark).where(
            EventBookmark.user_id == user_id
        ).options(
            selectinload(EventBookmark.event).selectinload(Event.images),
            selectinload(EventBookmark.event).selectinload(Event.category),
            selectinload(EventBookmark.event).selectinload(Event.organizer),
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_user_and_event(self, user_id: str, event_id: str) -> Optional[EventBookmark]:
        query = select(EventBookmark).where(
            and_(EventBookmark.user_id == user_id, EventBookmark.event_id == event_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
