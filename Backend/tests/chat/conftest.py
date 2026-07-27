import asyncio

import pytest
from sqlalchemy import delete

from app.database import SessionLocal
from app.chat.models import ChatMessage, ChatParticipant, ChatRoom, MessageRead
from app.events.models import Event, EventCategory, EventImage
from app.rewards.models import EventParticipation


@pytest.fixture(autouse=True)
def clean_chat_and_event_tables():
    """Truncate chat/event tables to keep websocket tests isolated."""

    async def _cleanup():
        async with SessionLocal() as session:
            for model in (
                ChatMessage,
                MessageRead,
                ChatParticipant,
                ChatRoom,
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

