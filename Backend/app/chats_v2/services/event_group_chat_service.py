from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils.auth_checks import is_admin
from app.chat.models import ChatParticipantRole, ChatParticipant, ChatRoom
from app.events.models import Event
from app.events.models.event_status import EventStatus
from app.rewards.models import EventParticipation
from app.tickets.models import Ticket, TicketStatus


class EventGroupChatError(Exception):
    """Raised when a user cannot join or interact with an event group chat."""


@dataclass
class EventGroupJoinResult:
    room_id: str
    event_id: str
    role: str


class EventGroupChatService:
    """Authorization and room resolution for event group chats."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_event(self, event_id: str) -> Event | None:
        return await self._session.get(Event, event_id)

    async def _get_user(self, user_id: str) -> User | None:
        return await self._session.get(User, user_id)

    async def _is_participant(self, event_id: str, user_id: str) -> bool:
        """Check if user is a participant via EventParticipation, Ticket, or ChatParticipant."""
        # First check if user is already a ChatParticipant in the event group room
        # (this covers auto-added users like ticket holders, organizer, admins)
        room_stmt = select(ChatRoom.id).where(
            and_(ChatRoom.event_id == event_id, ChatRoom.room_type == "event_group")
        )
        room_id = await self._session.scalar(room_stmt)
        if room_id:
            participant_stmt = select(ChatParticipant.id).where(
                and_(ChatParticipant.room_id == room_id, ChatParticipant.user_id == user_id)
            )
            if await self._session.scalar(participant_stmt):
                return True
        
        # Check EventParticipation
        participation_stmt = select(EventParticipation.id).where(
            and_(EventParticipation.event_id == event_id, EventParticipation.user_id == user_id)
        )
        if await self._session.scalar(participation_stmt):
            return True
        
        # Check if user has a valid ticket for the event
        ticket_stmt = select(Ticket.id).where(
            and_(
                Ticket.event_id == event_id,
                Ticket.owner_id == user_id,
                Ticket.status.in_([TicketStatus.ISSUED.value, TicketStatus.CHECKED_IN.value])
            )
        )
        if await self._session.scalar(ticket_stmt):
            return True
        
        return False

    @staticmethod
    def event_is_over(event: Event) -> bool:
        end_time = event.end_time or datetime.max.time()
        end_dt = datetime.combine(event.end_date, end_time)
        return datetime.utcnow() > end_dt

    @staticmethod
    def _validate_event_id(event_id: str) -> None:
        try:
            uuid.UUID(str(event_id))
        except ValueError as exc:
            raise EventGroupChatError("Invalid event id") from exc

    async def prepare_group_join(self, user_id: str, event_id: str) -> EventGroupJoinResult:
        self._validate_event_id(event_id)
        user = await self._get_user(user_id)
        if not user:
            raise EventGroupChatError("Unauthorized")

        event = await self.get_event(event_id)
        if not event:
            raise EventGroupChatError("Event not found")
        if event.status != EventStatus.APPROVED.value:
            raise EventGroupChatError("Event is not approved")
        if self.event_is_over(event):
            raise EventGroupChatError("Event has ended")

        role = ChatParticipantRole.PARTICIPANT.value
        if is_admin(user) or event.organizer_id == user.id:
            role = ChatParticipantRole.OWNER.value
        elif not await self._is_participant(event.id, user.id):
            raise EventGroupChatError("Not a participant")

        room_id = f"event:group:{event.id}"
        return EventGroupJoinResult(room_id=room_id, event_id=event.id, role=role)
