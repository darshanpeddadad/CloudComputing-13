from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import EventCategory


class CategoryRepository:
    """Persistence operations for event categories."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_categories(self) -> List[EventCategory]:
        """List all event categories, ordered by name."""
        stmt = select(EventCategory).order_by(EventCategory.name.asc())
        result = await self.session.scalars(stmt)
        return list(result.all())
