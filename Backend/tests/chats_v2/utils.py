import asyncio
import uuid
from datetime import date, datetime, time as dtime, timedelta
from typing import Optional

import socketio
from fastapi.testclient import TestClient

from app.auth.models import Role, User
from app.database import SessionLocal
from app.events.models import Event, EventCategory, EventStatus
from app.tickets.models import Ticket, TicketType
from app.rewards.models import EventParticipation, ParticipationStatus
from Backend.tests.auth.utils import auth_url, registration_payload


def register_and_login(client: TestClient) -> dict:
    """Register a user and return user info plus access token."""
    registration = registration_payload()
    password = registration["password"]
    register_response = client.post(auth_url("/register"), json=registration)
    assert register_response.status_code == 201

    login_response = client.post(
        auth_url("/login"),
        json={"email": registration["email"], "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    return {
        "user": data["user"],
        "token": data["access_token"],
    }


async def promote_to_admin(user_id: str) -> None:
    """Ensure the given user has the admin role."""
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        # Query by name instead of ID, since role IDs may vary
        stmt = select(Role).where(Role.name == "admin")
        result = await session.scalars(stmt)
        role = result.first()
        if not role:
            # If role doesn't exist, create it with a generated ID
            import uuid
            role = Role(id=f"role-admin-{uuid.uuid4().hex[:6]}", name="admin")
            session.add(role)
            await session.flush([role])
        user = await session.get(User, user_id)
        assert user is not None
        await session.refresh(user, attribute_names=["roles"])
        if role not in user.roles:
            user.roles.append(role)
        await session.commit()


async def create_event(
    organizer_id: str,
    *,
    ends_in_past: bool = False,
    status: EventStatus = EventStatus.PENDING,
) -> Event:
    """Create an event for chat tests."""
    async with SessionLocal() as session:
        category = EventCategory(id=str(uuid.uuid4()), name=f"Categ-{uuid.uuid4().hex[:6]}")
        today = date.today()
        if ends_in_past:
            start = today - timedelta(days=1)
            end = today - timedelta(days=1)
            end_time_value = (datetime.utcnow() - timedelta(hours=1)).time()
        else:
            start = today + timedelta(days=1)
            end = today + timedelta(days=1)
            end_time_value = dtime(12, 0)
        event = Event(
            id=str(uuid.uuid4()),
            title="Socket.IO Test Event",
            description="Chat v2 flow validation.",
            location="Fulda",
            latitude=50.55,
            longitude=9.67,
            start_date=start,
            end_date=end,
            start_time=dtime(10, 0),
            end_time=end_time_value,
            sos_enabled=False,
            max_attendees=50,
            status=status.value,
            organizer_id=organizer_id,
            category=category,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


async def add_participation(event_id: str, user_id: str) -> None:
    """Mark a user as a participant for an event."""
    async with SessionLocal() as session:
        participation = EventParticipation(
            id=str(uuid.uuid4()),
            event_id=event_id,
            user_id=user_id,
            status=ParticipationStatus.REGISTERED.value,
        )
        session.add(participation)
        await session.commit()


async def issue_ticket(event_id: str, user_id: str) -> Ticket:
    """Create a ticket (attendee) for the given event and user using the service flow (auto-adds to chat)."""
    from app.tickets.repositories import TicketRepository
    from app.tickets.services.ticket_service import TicketService
    async with SessionLocal() as session:
        # ensure ticket type exists
        ticket_type = TicketType(
            id=str(uuid.uuid4()),
            event_id=event_id,
            name="General Admission",
            price=0,
            currency="USD",
            capacity=100,
            max_per_user=None,
        )
        session.add(ticket_type)
        await session.flush([ticket_type])

        service = TicketService(session, TicketRepository(session))
        ticket, point_result, redemption_info = await service.purchase_ticket(event_id=event_id, ticket_type_id=ticket_type.id, buyer_id=user_id)
        await session.commit()
        await session.refresh(ticket)
        return ticket


class DirectSocketClient:
    """Async Socket.IO test client wrapper for direct chat flows."""

    def __init__(self, base_url: str, token: str):
        self._base_url = base_url
        self._token = token
        self._client = socketio.AsyncClient()
        self.joined = asyncio.Queue()
        self.messages = asyncio.Queue()
        self.errors = asyncio.Queue()
        self._client.on("direct:joined", self._on_joined)
        self._client.on("direct:message", self._on_message)
        self._client.on("direct:error", self._on_error)

    async def _on_joined(self, data):
        await self.joined.put(data)

    async def _on_message(self, data):
        await self.messages.put(data)

    async def _on_error(self, data):
        await self.errors.put(data)

    async def connect(self) -> None:
        await self._client.connect(
            self._base_url,
            socketio_path="/socket.io",
            transports=["websocket"],
            auth={"token": self._token},
        )

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def join_direct(self, target_user_id: str, *, event_id: Optional[str] = None) -> None:
        await self._client.emit(
            "direct:join",
            {"target_user_id": target_user_id, "event_id": event_id},
        )

    async def send_message(self, room_id: str, content: str) -> None:
        await self._client.emit(
            "direct:message",
            {"room_id": room_id, "content": content},
        )

    async def next_joined(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.joined.get(), timeout=timeout)

    async def next_message(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.messages.get(), timeout=timeout)

    async def next_error(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.errors.get(), timeout=timeout)

    async def poll_message(self, timeout: float = 0.3) -> Optional[dict]:
        """Return next message or None if none received within timeout."""
        try:
            return await asyncio.wait_for(self.messages.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def poll_error(self, timeout: float = 0.3) -> Optional[dict]:
        """Return next error or None if none received within timeout."""
        try:
            return await asyncio.wait_for(self.errors.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


class EventGroupSocketClient:
    """Async Socket.IO test client wrapper for event group chat flows."""

    def __init__(self, base_url: str, token: str):
        self._base_url = base_url
        self._token = token
        self._client = socketio.AsyncClient()
        self.joined = asyncio.Queue()
        self.messages = asyncio.Queue()
        self.errors = asyncio.Queue()
        self.participants = asyncio.Queue()
        self.ended = asyncio.Queue()
        self._client.on("event_group:joined", self._on_joined)
        self._client.on("event_group:message", self._on_message)
        self._client.on("event_group:error", self._on_error)
        self._client.on("event_group:participants", self._on_participants)
        self._client.on("event_group:ended", self._on_ended)

    async def _on_joined(self, data):
        await self.joined.put(data)

    async def _on_message(self, data):
        await self.messages.put(data)

    async def _on_error(self, data):
        await self.errors.put(data)

    async def _on_participants(self, data):
        await self.participants.put(data)

    async def _on_ended(self, data):
        await self.ended.put(data)

    async def connect(self) -> None:
        await self._client.connect(
            self._base_url,
            socketio_path="/socket.io",
            transports=["websocket"],
            auth={"token": self._token},
        )

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def join_event(self, event_id: str) -> None:
        await self._client.emit(
            "event_group:join",
            {"event_id": event_id},
        )

    async def send_message(self, room_id: str, content: str) -> None:
        await self._client.emit(
            "event_group:message",
            {"room_id": room_id, "content": content},
        )

    async def leave(self, room_id: Optional[str] = None, event_id: Optional[str] = None) -> None:
        await self._client.emit(
            "event_group:leave",
            {"room_id": room_id, "event_id": event_id},
        )

    async def next_joined(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.joined.get(), timeout=timeout)

    async def next_message(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.messages.get(), timeout=timeout)

    async def next_participants(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.participants.get(), timeout=timeout)

    async def next_error(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.errors.get(), timeout=timeout)

    async def next_ended(self, timeout: float = 3.0) -> dict:
        return await asyncio.wait_for(self.ended.get(), timeout=timeout)

    async def poll_message(self, timeout: float = 0.3) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self.messages.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def poll_error(self, timeout: float = 0.3) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self.errors.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def poll_participants(self, timeout: float = 0.3) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self.participants.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def poll_ended(self, timeout: float = 0.3) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self.ended.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
