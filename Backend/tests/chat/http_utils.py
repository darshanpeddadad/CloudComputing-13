import asyncio
import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Sequence, Tuple

from fastapi.testclient import TestClient

from app.auth.models import User
from app.chat.models import ChatMessage, ChatRoom
from app.chat.services import ChatService
from app.database import SessionLocal
from app.events.models import Event, EventCategory, EventStatus
from app.rewards.models import EventParticipation, ParticipationStatus
from Backend.tests.auth.utils import auth_url, registration_payload

MessageSpec = Tuple[str, str, Optional[datetime]]


def register_and_login(client: TestClient) -> dict:
    """Register and log in a user, returning id/token/headers."""
    payload = registration_payload()
    password = payload["password"]
    register_response = client.post(auth_url("/register"), json=payload)
    assert register_response.status_code == 201

    login_response = client.post(
        auth_url("/login"),
        json={"email": payload["email"], "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    token = data["access_token"]
    return {
        "user": data["user"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


async def _load_user(session, user_id: str) -> User:
    user = await session.get(User, user_id)
    assert user is not None, f"User {user_id} not found"
    return user


def seed_event_chat(
    organizer_id: str,
    participant_id: str,
    message_specs: Optional[Sequence[MessageSpec]] = None,
) -> Tuple[Event, ChatRoom, List[ChatMessage]]:
    """Create an event, enroll a participant, create the group room, and seed messages."""
    now = datetime.utcnow()
    specs = list(message_specs or [
        (participant_id, "group hello", now - timedelta(seconds=30)),
        (participant_id, "group follow-up", now),
    ])

    async def _run():
        async with SessionLocal() as session:
            category = EventCategory(id=str(uuid.uuid4()), name=f"Categ-{uuid.uuid4().hex[:6]}")
            tomorrow = date.today() + timedelta(days=1)
            event = Event(
                id=str(uuid.uuid4()),
                title="Chat Event",
                description="Event chat setup",
                location="Fulda",
                latitude=50.55,
                longitude=9.67,
                start_date=tomorrow,
                end_date=tomorrow,
                start_time=time(10, 0),
                end_time=time(12, 0),
                sos_enabled=False,
                status=EventStatus.APPROVED.value,
                max_attendees=25,
                organizer_id=organizer_id,
                category=category,
            )
            session.add(event)
            session.add(
                EventParticipation(
                    id=str(uuid.uuid4()),
                    event_id=event.id,
                    user_id=participant_id,
                    status=ParticipationStatus.REGISTERED.value,
                )
            )
            await session.flush([event, category])

            service = ChatService(session)
            organizer = await _load_user(session, organizer_id)
            participant = await _load_user(session, participant_id)
            room = await service.ensure_event_group_room(event, organizer)
            await service.sync_event_room_members(room, event)

            messages: List[ChatMessage] = []
            for sender_id, content, sent_at in specs:
                sender = await _load_user(session, sender_id)
                msg = await service.save_message(room, sender, content)
                if sent_at:
                    msg.sent_at = sent_at
                messages.append(msg)

            await session.commit()
            for msg in messages:
                await session.refresh(msg)
            await session.refresh(event)
            await session.refresh(room)
            return event, room, messages

    return asyncio.run(_run())


def seed_direct_chat(
    initiator_id: str,
    target_id: str,
    *,
    context: str = "admin",
    message_specs: Optional[Sequence[MessageSpec]] = None,
) -> Tuple[ChatRoom, List[ChatMessage]]:
    """Create a direct room and seed messages for two users."""
    now = datetime.utcnow()
    specs = list(message_specs or [(target_id, "dm hello", now)])

    async def _run():
        async with SessionLocal() as session:
            service = ChatService(session)
            initiator = await _load_user(session, initiator_id)
            target = await _load_user(session, target_id)
            room = await service.get_or_create_direct_room(
                initiator,
                target,
                context,
                metadata_json={"context": context},
            )

            messages: List[ChatMessage] = []
            for sender_id, content, sent_at in specs:
                sender = await _load_user(session, sender_id)
                msg = await service.save_message(room, sender, content)
                if sent_at:
                    msg.sent_at = sent_at
                messages.append(msg)

            await session.commit()
            for msg in messages:
                await session.refresh(msg)
            await session.refresh(room)
            return room, messages

    return asyncio.run(_run())
