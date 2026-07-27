import asyncio
import uuid
from datetime import date, time, timedelta

import pytest
from sqlalchemy import delete

from app.database import SessionLocal
from app.chat.models import ChatMessage, ChatParticipant, ChatRoom, MessageRead
from app.events.models import Event, EventCategory, EventImage, EventStatus
from app.rewards.models import EventParticipation
from app.tickets.models import Ticket, TicketType, TicketTransaction
from app.resale.models import TicketResaleListing
from tests.events.utils import create_event_with_dependencies


@pytest.fixture(autouse=True)
def clean_ticket_related_tables():
    """Clear ticket, event, and chat tables between tests for isolation."""

    async def _cleanup():
        async with SessionLocal() as session:
            for model in (
                MessageRead,
                ChatMessage,
                ChatParticipant,
                ChatRoom,
                TicketResaleListing,
                TicketTransaction,
                Ticket,
                TicketType,
                EventParticipation,
                EventImage,
                Event,
                EventCategory,
            ):
                await session.execute(delete(model))
            await session.commit()

    asyncio.run(_cleanup())
    yield
    asyncio.run(_cleanup())


@pytest.fixture()
def approved_event_with_ticket_type():
    """Create an approved event along with a ticket type for purchases."""

    def _create_event(**overrides):
        async def _run():
            async with SessionLocal() as session:
                event_kwargs = dict(overrides)
                event_kwargs.setdefault("status", EventStatus.APPROVED.value)
                future_date = date.today() + timedelta(days=1)
                event_kwargs.setdefault("start_date", future_date)
                event_kwargs.setdefault("end_date", future_date)
                event_kwargs.setdefault("start_time", time(10, 0))
                event_kwargs.setdefault("end_time", time(18, 0))

                event_payload = await create_event_with_dependencies(session, **event_kwargs)
                event = event_payload["event"]
                ticket_type = TicketType(
                    id=str(uuid.uuid4()),
                    event_id=event.id,
                    name="General Admission",
                    price=25.00,
                    currency="USD",
                    capacity=100,
                )
                session.add(ticket_type)
                await session.commit()
                await session.refresh(event)
                await session.refresh(ticket_type)
                return {"event": event, "ticket_type": ticket_type, **event_payload}

        return asyncio.run(_run())

    return _create_event
