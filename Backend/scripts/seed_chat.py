import asyncio
import sys
import uuid
from datetime import date, time, timedelta
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import func, select

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.auth.models import Role, User  # noqa: E402
from app.auth.security.auth_security import AuthSecurity  # noqa: E402
from app.chat.models import ChatMessage, ChatParticipantRole  # noqa: E402
from app.chat.services import ChatService  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.events.models import Event, EventStatus  # noqa: E402
from app.interests.models import Interest  # noqa: F401, E402
from app.seeders.auth_seed import seed_roles_and_admin  # noqa: E402
from app.seeders.event_category_seed import seed_event_categories  # noqa: E402
from app.seeders.event_user_seed import seed_event_users  # noqa: E402


async def _get_or_create_chat_event(session, organizer: User, category_id: str) -> Event:
    existing = await session.scalar(select(Event).where(Event.title == "Chat Demo Event"))
    if existing:
        return existing

    today = date.today()
    event = Event(
        id=str(uuid.uuid4()),
        title="Chat Demo Event",
        description="Seeded event with chat data",
        location="Fulda Innovation Center",
        latitude=50.55,
        longitude=9.68,
        start_date=today + timedelta(days=1),
        end_date=today + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(12, 0),
        sos_enabled=False,
        status=EventStatus.APPROVED.value,
        max_attendees=120,
        organizer_id=organizer.id,
        category_id=category_id,
    )
    session.add(event)
    await session.flush([event])
    return event


async def _seed_event_room(service: ChatService, event: Event, user_a: User, user_b: User) -> None:
    room = await service.ensure_event_group_room(event, user_a)
    await service.sync_event_room_members(room, event)
    await service.ensure_participant(room, user_a, ChatParticipantRole.OWNER)
    await service.ensure_participant(room, user_b, ChatParticipantRole.PARTICIPANT)

    existing = await service.session.scalar(
        select(func.count()).select_from(ChatMessage).where(ChatMessage.room_id == room.id)
    )
    if not existing:
        await service.save_message(room, user_a, "Welcome to the event chat!")
        await service.save_message(room, user_b, "Thanks for adding me, looks great.")
        await service.save_message(room, user_a, "Feel free to ask anything about the event.")


async def _seed_direct_room(service: ChatService, event: Event, user_a: User, user_b: User) -> None:
    context = f"event:{event.id}"
    room = await service.get_or_create_direct_room(
        user_a,
        user_b,
        context,
        metadata_json={"context": context, "event_id": event.id, "target_user_id": user_b.id},
    )
    await service.ensure_participant(room, user_a, ChatParticipantRole.PARTICIPANT)
    await service.ensure_participant(room, user_b, ChatParticipantRole.PARTICIPANT)
    await service.densify_admin_as_owner(room, user_a)

    existing = await service.session.scalar(
        select(func.count()).select_from(ChatMessage).where(ChatMessage.room_id == room.id)
    )
    if not existing:
        await service.save_message(room, user_a, "Hey, wanted to sync on event logistics.")
        await service.save_message(room, user_b, "Sure, I’m on it. Will share updates here.")


async def main() -> None:
    load_dotenv(project_root / ".env")
    await init_db()

    auth_security = AuthSecurity()
    async with SessionLocal() as session:
        # Ensure roles/users/categories exist
        await seed_roles_and_admin(session, auth_security)
        user_role = await session.scalar(select(Role).where(Role.name == "user"))
        organizers = await seed_event_users(session, auth_security, user_role, target_count=2)
        categories = await seed_event_categories(session)
        await session.flush()

        user_a, user_b = organizers[0], organizers[1]
        category = categories[0]

        event = await _get_or_create_chat_event(session, user_a, category.id)

        # Ensure participant entry for user_b
        from app.rewards.models import EventParticipation, ParticipationStatus  # noqa: E402

        existing_participation = await session.scalar(
            select(EventParticipation).where(
                EventParticipation.event_id == event.id, EventParticipation.user_id == user_b.id
            )
        )
        if not existing_participation:
            session.add(
                EventParticipation(
                    id=str(uuid.uuid4()),
                    event_id=event.id,
                    user_id=user_b.id,
                    status=ParticipationStatus.REGISTERED.value,
                )
            )

        service = ChatService(session)
        await _seed_event_room(service, event, user_a, user_b)
        await _seed_direct_room(service, event, user_a, user_b)
        await session.commit()

        print("Seeded chat data: event group chat and direct chat between two seeded users.")


if __name__ == "__main__":
    asyncio.run(main())
