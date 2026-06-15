from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils.auth_checks import is_admin
from app.events.models import Event
from app.rewards.models import EventParticipation


class DirectChatError(Exception):
    """Raised for validation failures when joining direct chats."""


@dataclass
class DirectJoinResult:
    room_id: str
    context: str
    event_id: Optional[str]
    target_user_id: str


def _build_room_id(user_id: str, target_id: str, context: str) -> str:
    left, right = sorted([user_id, target_id])
    return f"direct:{context}:{left}:{right}"


class DirectChatService:
    """Encapsulates v2 direct chat authorization and room key logic."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _get_user(self, user_id: str) -> Optional[User]:
        return await self._session.get(User, user_id)

    async def _get_event(self, event_id: str) -> Optional[Event]:
        return await self._session.get(Event, event_id)

    async def _is_participant(self, event_id: str, user_id: str) -> bool:
        stmt = select(EventParticipation.id).where(
            and_(EventParticipation.event_id == event_id, EventParticipation.user_id == user_id)
        )
        result = await self._session.scalar(stmt)
        return result is not None

    @staticmethod
    def _event_is_over(event: Event) -> bool:
        end_time = event.end_time or datetime.max.time()
        end_dt = datetime.combine(event.end_date, end_time)
        return datetime.utcnow() > end_dt

    async def _validate_target(self, target_user_id: str) -> User:
        target = await self._get_user(target_user_id)
        if not target:
            raise DirectChatError("Recipient not found")
        return target

    async def _validate_event(self, event_id: Optional[str]) -> Optional[Event]:
        if not event_id:
            return None
        event = await self._get_event(event_id)
        if not event:
            raise DirectChatError("Event not found")
        return event

    async def prepare_direct_join(
        self,
        user_id: str,
        target_user_id: str,
        event_id: Optional[str],
    ) -> DirectJoinResult:
        """Validate access and derive room/context for a direct chat."""
        user = await self._get_user(user_id)
        if not user:
            raise DirectChatError("Unauthorized")
        target = await self._validate_target(target_user_id)
        event = await self._validate_event(event_id)

        user_is_admin = is_admin(user)
        target_is_admin = is_admin(target)

        if user_is_admin or target_is_admin:
            context = "admin"
            room_id = _build_room_id(user.id, target.id, context)
            return DirectJoinResult(room_id=room_id, context=context, event_id=None, target_user_id=target.id)

        # Non-admins require event context
        if not event:
            raise DirectChatError("Event context is required")

        event_is_over = self._event_is_over(event)

        # Organizer targeted by attendee/outsider
        if target.id == event.organizer_id:
            if event_is_over:
                raise DirectChatError("Event has ended; direct chat disabled")
            context = f"event:{event.id}"
            room_id = _build_room_id(user.id, target.id, context)
            return DirectJoinResult(room_id=room_id, context=context, event_id=event.id, target_user_id=target.id)

        # Organizer initiating to someone else (can DM anyone when event is active)
        if user.id == event.organizer_id:
            if event_is_over:
                raise DirectChatError("Event has ended; direct chat disabled")
            context = f"event:{event.id}"
            room_id = _build_room_id(user.id, target.id, context)
            return DirectJoinResult(room_id=room_id, context=context, event_id=event.id, target_user_id=target.id)

        # Other cases (non-organizer to non-organizer) are not allowed in v2
        raise DirectChatError("Organizer only")
