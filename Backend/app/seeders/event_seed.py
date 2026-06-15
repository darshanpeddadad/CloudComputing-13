import uuid
from dataclasses import dataclass
from datetime import date, timedelta, time
from typing import List, Sequence

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.events.models import Event, EventCategory, EventImage, EventStatus
from app.seeders.event_category_seed import seed_event_categories

faker = Faker()

TOTAL_EVENTS = 50
APPROVED_EVENTS = 25
PENDING_EVENTS = 15
REJECTED_EVENTS = TOTAL_EVENTS - APPROVED_EVENTS - PENDING_EVENTS
IMAGE_URLS: Sequence[str] = (
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-1.jpg",
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-2.jpg",
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-3.jpg",
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-4.jpg",
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-5.jpg",
    "https://fuldanexusimage.s3.eu-central-1.amazonaws.com/images/default-6.jpg",
)


@dataclass(frozen=True)
class EventSeriesTemplate:
    location: str
    category_name: str
    latitude: float
    longitude: float
    base_capacity: int


@dataclass(frozen=True)
class EventScheduleTemplate:
    days_from_today: int
    duration_days: int
    start_hour: int
    duration_hours: int
    capacity_delta: int
    sos_enabled: bool
    image_count: int


@dataclass(frozen=True)
class EventBlueprint:
    organizer_index: int
    location: str
    latitude: float
    longitude: float
    category_name: str
    days_from_today: int
    duration_days: int
    start_hour: int
    duration_hours: int
    max_attendees: int
    sos_enabled: bool
    image_count: int
    status: str


EVENT_SERIES_TEMPLATES: Sequence[EventSeriesTemplate] = (
    EventSeriesTemplate(
        location="Fulda Innovation Center Hall A",
        category_name="summit",
        latitude=50.5553,
        longitude=9.6801,
        base_capacity=320,
    ),
    EventSeriesTemplate(
        location="Fulda Tech Park Pavilion",
        category_name="expo",
        latitude=50.5462,
        longitude=9.6991,
        base_capacity=450,
    ),
    EventSeriesTemplate(
        location="Fulda Cultural Hub Atrium",
        category_name="social",
        latitude=50.5521,
        longitude=9.6729,
        base_capacity=280,
    ),
    EventSeriesTemplate(
        location="Fulda Campus Lab 3",
        category_name="meetup",
        latitude=50.5586,
        longitude=9.6844,
        base_capacity=180,
    ),
    EventSeriesTemplate(
        location="Fulda Data Center West",
        category_name="workshop",
        latitude=50.5512,
        longitude=9.6912,
        base_capacity=220,
    ),
    EventSeriesTemplate(
        location="City Hall Fulda Chamber",
        category_name="forum",
        latitude=50.5544,
        longitude=9.6755,
        base_capacity=260,
    ),
    EventSeriesTemplate(
        location="Fulda Exchange Theater",
        category_name="showcase",
        latitude=50.5498,
        longitude=9.6687,
        base_capacity=300,
    ),
    EventSeriesTemplate(
        location="Fulda Startup Loft",
        category_name="party",
        latitude=50.5475,
        longitude=9.6821,
        base_capacity=200,
    ),
    EventSeriesTemplate(
        location="Fulda Civic Center Ballroom",
        category_name="conference",
        latitude=50.5567,
        longitude=9.6703,
        base_capacity=340,
    ),
    EventSeriesTemplate(
        location="Fulda Sports Pavilion",
        category_name="sports",
        latitude=50.5602,
        longitude=9.6779,
        base_capacity=400,
    ),
)

EVENT_SCHEDULE_TEMPLATES: Sequence[EventScheduleTemplate] = (
    EventScheduleTemplate(
        days_from_today=3,
        duration_days=0,
        start_hour=9,
        duration_hours=3,
        capacity_delta=0,
        sos_enabled=True,
        image_count=2,
    ),
    EventScheduleTemplate(
        days_from_today=10,
        duration_days=0,
        start_hour=11,
        duration_hours=2,
        capacity_delta=-30,
        sos_enabled=False,
        image_count=1,
    ),
    EventScheduleTemplate(
        days_from_today=18,
        duration_days=1,
        start_hour=10,
        duration_hours=4,
        capacity_delta=50,
        sos_enabled=True,
        image_count=2,
    ),
    EventScheduleTemplate(
        days_from_today=26,
        duration_days=0,
        start_hour=17,
        duration_hours=3,
        capacity_delta=-20,
        sos_enabled=False,
        image_count=1,
    ),
    EventScheduleTemplate(
        days_from_today=35,
        duration_days=2,
        start_hour=13,
        duration_hours=5,
        capacity_delta=120,
        sos_enabled=True,
        image_count=3,
    ),
)


def _build_status_plan() -> Sequence[str]:
    counts = {
        EventStatus.APPROVED.value: APPROVED_EVENTS,
        EventStatus.PENDING.value: PENDING_EVENTS,
        EventStatus.REJECTED.value: REJECTED_EVENTS,
    }
    rotation = [
        EventStatus.APPROVED.value,
        EventStatus.PENDING.value,
        EventStatus.APPROVED.value,
        EventStatus.REJECTED.value,
    ]
    plan: List[str] = []
    while len(plan) < TOTAL_EVENTS:
        for status in rotation:
            if counts[status] > 0:
                plan.append(status)
                counts[status] -= 1
                if len(plan) == TOTAL_EVENTS:
                    break
    return tuple(plan)


STATUS_PLAN: Sequence[str] = _build_status_plan()


def _build_event_blueprints() -> Sequence[EventBlueprint]:
    expected_total = len(EVENT_SERIES_TEMPLATES) * len(EVENT_SCHEDULE_TEMPLATES)
    if expected_total != TOTAL_EVENTS:
        raise RuntimeError("Event template configuration does not match TOTAL_EVENTS.")
    if len(STATUS_PLAN) != TOTAL_EVENTS:
        raise RuntimeError("Status plan does not cover TOTAL_EVENTS.")

    blueprints: List[EventBlueprint] = []
    status_index = 0
    for organizer_index, series in enumerate(EVENT_SERIES_TEMPLATES):
        for schedule in EVENT_SCHEDULE_TEMPLATES:
            max_attendees = max(50, series.base_capacity + schedule.capacity_delta)
            blueprints.append(
                EventBlueprint(
                    organizer_index=organizer_index,
                    location=series.location,
                    latitude=series.latitude,
                    longitude=series.longitude,
                    category_name=series.category_name,
                    days_from_today=schedule.days_from_today,
                    duration_days=schedule.duration_days,
                    start_hour=schedule.start_hour,
                    duration_hours=schedule.duration_hours,
                    max_attendees=max_attendees,
                    sos_enabled=schedule.sos_enabled,
                    image_count=schedule.image_count,
                    status=STATUS_PLAN[status_index],
                )
            )
            status_index += 1
    return tuple(blueprints)


EVENT_BLUEPRINTS: Sequence[EventBlueprint] = _build_event_blueprints()


async def seed_event_users_and_events(session: AsyncSession, organizers: List[User]):
    """Seed categories and sample events for existing organizers."""
    categories = await seed_event_categories(session)

    existing_event = await session.scalar(select(Event.id))
    if existing_event:
        return None, "events_exist"

    if not organizers:
        return None, "no_organizers"

    await _create_events(session, organizers, categories)
    return (len(organizers), len(categories), TOTAL_EVENTS), "seeded"

async def _create_events(session: AsyncSession, organizers: List[User], categories: List[EventCategory]) -> None:
    if len(organizers) < len(EVENT_SERIES_TEMPLATES):
        raise ValueError("Insufficient organizers to cover planned event assignments.")

    category_lookup = {category.name: category for category in categories}
    required_categories = {blueprint.category_name for blueprint in EVENT_BLUEPRINTS}
    existing_categories = set(category_lookup.keys())
    missing_categories = sorted(required_categories - existing_categories)
    if missing_categories:
        raise ValueError(f"Missing event categories for seeding: {', '.join(missing_categories)}")

    base_date = date.today()
    for index, blueprint in enumerate(EVENT_BLUEPRINTS):
        organizer = organizers[blueprint.organizer_index]
        category = category_lookup[blueprint.category_name]

        # Use a fixed seed per event index for deterministic faker output
        # Create a new Faker instance with seed for each event
        event_faker = Faker(seed=42 + index)
        title = event_faker.catch_phrase()
        description = event_faker.paragraph(nb_sentences=3)

        start_date = base_date + timedelta(days=blueprint.days_from_today)
        end_date = start_date + timedelta(days=blueprint.duration_days)
        start_time = time(hour=blueprint.start_hour, minute=0)
        end_hour = min(blueprint.start_hour + blueprint.duration_hours, 23)
        end_time = time(hour=end_hour, minute=0)

        event = Event(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            location=blueprint.location,
            latitude=blueprint.latitude,
            longitude=blueprint.longitude,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            sos_enabled=blueprint.sos_enabled,
            max_attendees=blueprint.max_attendees,
            organizer_id=organizer.id,
            category_id=category.id,
            status=blueprint.status,
        )
        session.add(event)

        for position in range(blueprint.image_count):
            image_url = IMAGE_URLS[(index + position) % len(IMAGE_URLS)]
            session.add(
                EventImage(
                    id=str(uuid.uuid4()),
                    event_id=event.id,
                    url=image_url,
                    position=position,
                )
            )
    await session.commit()
