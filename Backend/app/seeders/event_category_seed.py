import uuid
from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.models import EventCategory

EVENT_CATEGORIES: Sequence[str] = (
    "conference",
    "social",
    "workshop",
    "sports",
    "meetup",
    "expo",
    "forum",
    "showcase",
    "party",
    "summit",
    "others",
)


async def seed_event_categories(session: AsyncSession) -> List[EventCategory]:
    """Ensure default event categories exist and return them."""
    categories: List[EventCategory] = []
    for name in EVENT_CATEGORIES:
        existing = await session.scalar(select(EventCategory).where(EventCategory.name == name))
        if existing:
            categories.append(existing)
        else:
            category = EventCategory(id=str(uuid.uuid4()), name=name)
            session.add(category)
            categories.append(category)
    await session.flush(categories)
    return categories
