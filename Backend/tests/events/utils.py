import uuid
from datetime import date, time
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.events.models import Event, EventCategory, EventEditRequest, EventImage, EventStatus

S3_IMAGE_URL = "https://s3.amazonaws.com/fulda-events/images/sample.jpg"


async def truncate_event_tables(session: AsyncSession) -> None:
    """Remove all event records to keep tests isolated."""
    await session.execute(delete(EventEditRequest))
    await session.execute(delete(EventImage))
    await session.execute(delete(Event))
    await session.execute(delete(EventCategory))


async def create_event_with_dependencies(
    session: AsyncSession,
    *,
    title: str = "Fulda Tech Fair",
    description: str = "A multi-day technology showcase.",
    location: str = "Fulda, Germany",
    latitude: float = 50.555,
    longitude: float = 9.679,
    start_date: date = date(2025, 5, 1),
    end_date: date = date(2025, 5, 1),
    start_time: time = time(10, 0),
    end_time: time = time(18, 0),
    category_name: str = "Technology",
    organizer_first_names: str = "Alex",
    organizer_last_name: str = "Organizer",
    sos_enabled: bool = True,
    max_attendees: int = 500,
    image_urls: Optional[Iterable[str]] = None,
    status: str = EventStatus.APPROVED.value,
) -> Dict:
    """Insert an event plus organizer/category/images; return created ORM entities."""
    organizer = User(
        id=str(uuid.uuid4()),
        first_names=organizer_first_names,
        last_name=organizer_last_name,
        email=f"{uuid.uuid4().hex}@fulda-events.test",
        dob="1995-01-01",
        password_hash="hashed-password",
        roles=[],
    )
    category = await _get_or_create_category(session, category_name)
    event = Event(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        location=location,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        sos_enabled=sos_enabled,
        max_attendees=max_attendees,
        status=EventStatus(status),
        category=category,
        organizer=organizer,
    )
    session.add_all([organizer, category, event])
    await session.flush()

    images: List[EventImage] = []
    for position, url in enumerate(image_urls or [S3_IMAGE_URL]):
        image = EventImage(id=str(uuid.uuid4()), event_id=event.id, url=url, position=position)
        images.append(image)
        session.add(image)

    return {"event": event, "organizer": organizer, "category": category, "images": images}


async def create_category(session: AsyncSession, name: str = "Technology") -> EventCategory:
    """Create or reuse a category by name for event tests."""
    category = await _get_or_create_category(session, name)
    await session.flush([category])
    return category


def make_event_payload(category_id: str, organizer_id: str, **overrides: Any) -> Dict[str, Any]:
    """Base JSON payload for creating events through the API."""
    payload: Dict[str, Any] = {
        "title": "Fulda Tech Meetup",
        "description": "Monthly meetup for Fulda students and alumni.",
        "location": "Fulda Innovation Lab",
        "latitude": 50.554,
        "longitude": 9.678,
        "start_date": date(2025, 6, 1).isoformat(),
        "end_date": date(2025, 6, 1).isoformat(),
        "start_time": time(10, 0).isoformat(),
        "end_time": time(13, 0).isoformat(),
        "category_id": category_id,
        "organizer_id": organizer_id,
        "sos_enabled": False,
        "max_attendees": 100,
        "image_urls": [S3_IMAGE_URL],
    }
    payload.update(overrides)
    return payload


async def count_events(session: AsyncSession) -> int:
    """Return the total number of events in the database."""
    total = await session.scalar(select(func.count(Event.id)))
    return int(total or 0)


async def create_event_for_user(
    session: AsyncSession,
    *,
    organizer: User,
    category: EventCategory,
    title: str = "Org Owned Event",
    description: str = "Organizer-created event",
    location: str = "Fulda Campus",
    latitude: float = 50.551,
    longitude: float = 9.678,
    start_date: date = date(2025, 6, 1),
    end_date: date = date(2025, 6, 1),
    start_time: time = time(10, 0),
    end_time: time = time(12, 0),
    sos_enabled: bool = False,
    max_attendees: int = 50,
    status: str = EventStatus.APPROVED.value,
) -> Event:
    """Create an event for an existing organizer and category."""
    event = Event(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        location=location,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        sos_enabled=sos_enabled,
        max_attendees=max_attendees,
        status=EventStatus(status),
        category=category,
        organizer=organizer,
    )
    session.add(event)
    await session.flush([event])
    return event


async def _get_or_create_category(session: AsyncSession, name: str) -> EventCategory:
    stmt = select(EventCategory).where(func.lower(EventCategory.name) == name.lower())
    result = await session.scalars(stmt)
    category = result.first()
    if category:
        return category
    category = EventCategory(id=str(uuid.uuid4()), name=name)
    session.add(category)
    await session.flush([category])
    return category
