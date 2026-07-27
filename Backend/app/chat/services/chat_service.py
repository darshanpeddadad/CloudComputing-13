from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.auth.utils import is_admin
from app.chat.models import (
    ChatMessage,
    ChatMessageType,
    ChatParticipant,
    ChatParticipantRole,
    ChatRoom,
    ChatRoomType,
)
from app.chat.schemas import (
    ChatMessageResponse,
    ChatParticipantSummary,
    ChatRoomSummary,
    ChatUserSummary,
    MarkReadResponse,
    UnreadRoomEntry,
    UnreadSummary,
)
from app.events.models import Event
from app.rewards.models import EventParticipation

ROLE_PRIORITY = {
    ChatParticipantRole.OWNER.value: 3,
    ChatParticipantRole.MODERATOR.value: 2,
    ChatParticipantRole.PARTICIPANT.value: 1,
}


def _event_end_datetime(event: Event) -> datetime:
    return datetime.combine(event.end_date, event.end_time)


def _build_direct_key(user_id: str, target_id: str, context: str) -> str:
    left, right = sorted([user_id, target_id])
    return f"{context}:{left}:{right}"


class ChatService:
    """Encapsulates chat room, participant, and message operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    def to_message_response(self, message: ChatMessage) -> ChatMessageResponse:
        sender_summary = self._user_summary(message.sender) if message.sender else None
        return ChatMessageResponse(
            id=message.id,
            room_id=message.room_id,
            sender_id=message.sender_id,
            content=message.content,
            sent_at=message.sent_at,
            sender=sender_summary,
        )

    async def get_event(self, event_id: str) -> Optional[Event]:
        stmt = select(Event).where(Event.id == event_id).options(selectinload(Event.organizer))
        result = await self._session.scalars(stmt)
        return result.first()

    async def is_event_participant(self, event_id: str, user_id: str) -> bool:
        stmt = select(EventParticipation.id).where(
            and_(EventParticipation.event_id == event_id, EventParticipation.user_id == user_id)
        )
        result = await self._session.scalar(stmt)
        return result is not None

    async def ensure_event_group_room(self, event: Event, created_by: User) -> ChatRoom:
        stmt = select(ChatRoom).where(
            and_(ChatRoom.event_id == event.id, ChatRoom.room_type == ChatRoomType.EVENT_GROUP.value)
        )
        result = await self._session.scalars(stmt)
        room = result.first()
        if room:
            return room

        room = ChatRoom(
            id=str(uuid.uuid4()),
            room_type=ChatRoomType.EVENT_GROUP.value,
            event_id=event.id,
            title=f"Event chat: {event.title}",
            created_by_id=created_by.id,
            topic=f"Group chat for {event.title}",
        )
        self._session.add(room)
        await self._session.flush([room])
        if event.organizer_id:
            await self.ensure_participant(room, event.organizer, ChatParticipantRole.OWNER)
        return room

    async def sync_event_room_members(self, room: ChatRoom, event: Event) -> None:
        """Ensure all event participants plus organizer are present in chat room."""
        stmt = (
            select(EventParticipation)
            .where(EventParticipation.event_id == event.id)
            .options(selectinload(EventParticipation.user))
        )
        participations = (await self._session.scalars(stmt)).all()
        for participation in participations:
            if participation.user:
                await self.ensure_participant(room, participation.user, ChatParticipantRole.PARTICIPANT)
        if event.organizer:
            await self.ensure_participant(room, event.organizer, ChatParticipantRole.OWNER)

    async def ensure_participant(
        self,
        room: ChatRoom,
        user: User,
        role: ChatParticipantRole = ChatParticipantRole.PARTICIPANT,
    ) -> ChatParticipant:
        stmt = select(ChatParticipant).where(
            and_(ChatParticipant.room_id == room.id, ChatParticipant.user_id == user.id)
        )
        result = await self._session.scalars(stmt)
        participant = result.first()
        if participant:
            if ROLE_PRIORITY[role.value] > ROLE_PRIORITY[participant.role]:
                participant.role = role.value
                await self._session.flush([participant])
            return participant

        participant = ChatParticipant(
            id=str(uuid.uuid4()),
            room_id=room.id,
            user_id=user.id,
            role=role.value,
        )
        self._session.add(participant)
        await self._session.flush([participant])
        return participant

    async def remove_participant(self, room: ChatRoom, user: User) -> None:
        """Remove a user from a chat room."""
        stmt = select(ChatParticipant).where(
            and_(ChatParticipant.room_id == room.id, ChatParticipant.user_id == user.id)
        )
        participant = (await self._session.scalars(stmt)).first()
        if participant:
            await self._session.delete(participant)
            await self._session.flush()

    async def densify_admin_as_owner(self, room: ChatRoom, user: User) -> None:
        if is_admin(user):
            await self.ensure_participant(room, user, ChatParticipantRole.OWNER)

    async def list_participants_payload(self, room_id: str) -> List[dict]:
        stmt = (
            select(ChatParticipant)
            .where(ChatParticipant.room_id == room_id)
            .options(selectinload(ChatParticipant.user))
        )
        participants = (await self._session.scalars(stmt)).all()
        payload: List[dict] = []
        for participant in participants:
            user = participant.user
            payload.append(
                {
                    "user_id": participant.user_id,
                    "role": participant.role,
                    "name": f"{user.first_names} {user.last_name}".strip() if user else None,
                }
            )
        return payload

    async def get_or_create_direct_room(
        self,
        user: User,
        target: User,
        context: str,
        metadata_json: Optional[dict] = None,
    ) -> ChatRoom:
        key = _build_direct_key(user.id, target.id, context)
        stmt = select(ChatRoom).where(ChatRoom.direct_key == key)
        result = await self._session.scalars(stmt)
        room = result.first()
        if room:
            return room

        room = ChatRoom(
            id=str(uuid.uuid4()),
            room_type=ChatRoomType.DIRECT.value,
            title=f"Chat with {target.first_names}",
            direct_key=key,
            created_by_id=user.id,
            metadata_json=metadata_json,
        )
        self._session.add(room)
        await self._session.flush([room])
        await self.ensure_participant(
            room, target, ChatParticipantRole.OWNER if is_admin(target) else ChatParticipantRole.PARTICIPANT
        )
        await self.ensure_participant(room, user, ChatParticipantRole.PARTICIPANT)
        return room

    async def direct_room_exists(self, user_id: str, target_id: str, context: str) -> bool:
        """Return True if a direct chat room already exists for the pair/context."""
        key = _build_direct_key(user_id, target_id, context)
        stmt = select(ChatRoom.id).where(ChatRoom.direct_key == key)
        result = await self._session.scalar(stmt)
        return result is not None

    async def save_message(
        self,
        room: ChatRoom,
        sender: User,
        content: str,
        message_type: ChatMessageType = ChatMessageType.TEXT,
    ) -> ChatMessage:
        message = ChatMessage(
            id=str(uuid.uuid4()),
            room_id=room.id,
            sender_id=sender.id,
            message_type=message_type.value,
            content=content,
        )
        self._session.add(message)
        await self._session.flush([message])
        return message

    async def event_and_target_for_direct(
        self, event_id: Optional[str], target_id: str
    ) -> Tuple[Optional[Event], Optional[User]]:
        event = None
        if event_id:
            event = await self.get_event(event_id)
        stmt = select(User).where(User.id == target_id).options(selectinload(User.roles))
        target = await self._session.scalar(stmt)
        return event, target

    @staticmethod
    def event_is_over(event: Event) -> bool:
        """Return True if the event has already ended (date and time)."""
        now = datetime.utcnow()
        if event.end_date < now.date():
            return True
        if event.end_date == now.date() and event.end_time <= now.time():
            return True
        return False

    async def get_participant(self, room_id: str, user_id: str) -> Optional[ChatParticipant]:
        stmt = (
            select(ChatParticipant)
            .where(and_(ChatParticipant.room_id == room_id, ChatParticipant.user_id == user_id))
            .options(selectinload(ChatParticipant.room))
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def list_room_summaries(self, user_id: str) -> List[ChatRoomSummary]:
        stmt = (
            select(ChatParticipant)
            .where(ChatParticipant.user_id == user_id)
            .options(
                selectinload(ChatParticipant.room).selectinload(ChatRoom.event),
                selectinload(ChatParticipant.room).selectinload(ChatRoom.participants).selectinload(
                    ChatParticipant.user
                ),
            )
        )
        participants = (await self._session.scalars(stmt)).all()
        summaries: List[ChatRoomSummary] = []
        for participant in participants:
            room = participant.room
            if not room:
                continue
            last_message = await self._last_message(room.id)
            unread = await self._unread_count(room.id, participant.last_read_at)
            context = None
            if room.metadata_json:
                context = room.metadata_json.get("context")
            participant_summaries = self._participant_summaries(room)
            other_user = self._other_user_summary(participant_summaries, current_user_id=user_id)
            summaries.append(
                ChatRoomSummary(
                    id=room.id,
                    room_type=room.room_type,
                    event_id=room.event_id,
                    context=context,
                    title=room.title,
                    unread_count=unread,
                    last_message=self.to_message_response(last_message) if last_message else None,
                    participants=participant_summaries,
                    other_user=other_user,
                )
            )

        summaries.sort(
            key=lambda summary: summary.last_message.sent_at if summary.last_message else datetime.min,
            reverse=True,
        )
        return summaries

    async def list_messages(
        self,
        room_id: str,
        *,
        limit: int = 20,
        before: Optional[datetime] = None,
    ) -> Tuple[List[ChatMessage], int, bool, Optional[datetime]]:
        total_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.room_id == room_id)
        total = await self._session.scalar(total_stmt) or 0

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .options(selectinload(ChatMessage.sender))
        )
        if before:
            stmt = stmt.where(ChatMessage.sent_at < before)
        stmt = stmt.order_by(ChatMessage.sent_at.desc()).limit(limit)
        result = await self._session.scalars(stmt)
        messages = list(result.all())

        filtered_count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.room_id == room_id)
        if before:
            filtered_count_stmt = filtered_count_stmt.where(ChatMessage.sent_at < before)
        filtered_total = await self._session.scalar(filtered_count_stmt) or 0
        has_more = len(messages) < filtered_total
        next_before = messages[-1].sent_at if has_more and messages else None
        return messages, total, has_more, next_before

    async def unread_summary(self, user_id: str) -> UnreadSummary:
        stmt = select(ChatParticipant).where(ChatParticipant.user_id == user_id)
        participants = (await self._session.scalars(stmt)).all()
        rooms: List[UnreadRoomEntry] = []
        total = 0
        for participant in participants:
            unread = await self._unread_count(participant.room_id, participant.last_read_at)
            rooms.append(UnreadRoomEntry(room_id=participant.room_id, unread=unread))
            total += unread
        return UnreadSummary(total=total, rooms=rooms)

    async def mark_room_read(self, room_id: str, user_id: str, message_id: str) -> Optional[MarkReadResponse]:
        participant = await self.get_participant(room_id, user_id)
        if not participant:
            return None

        message = await self._session.get(ChatMessage, message_id)
        if not message or message.room_id != room_id:
            return None

        if not participant.last_read_at or participant.last_read_at < message.sent_at:
            participant.last_read_at = message.sent_at
            await self._session.flush([participant])

        unread = await self._unread_count(room_id, participant.last_read_at)
        await self._session.commit()
        return MarkReadResponse(
            room_id=room_id,
            unread=unread,
            last_read_message_id=message.id,
        )

    async def _last_message(self, room_id: str) -> Optional[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.sent_at.desc())
            .limit(1)
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def _unread_count(self, room_id: str, last_read_at: Optional[datetime]) -> int:
        stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.room_id == room_id)
        if last_read_at:
            stmt = stmt.where(ChatMessage.sent_at > last_read_at)
        result = await self._session.scalar(stmt)
        return int(result or 0)

    def _participant_summaries(self, room: ChatRoom) -> List[ChatParticipantSummary]:
        summaries: List[ChatParticipantSummary] = []
        for participant in room.participants:
            name = self._user_name(participant.user) if participant.user else None
            summaries.append(
                ChatParticipantSummary(
                    user_id=participant.user_id,
                    role=participant.role,
                    name=name,
                )
            )
        return summaries

    def _other_user_summary(
        self, participants: List[ChatParticipantSummary], current_user_id: str
    ) -> Optional[ChatUserSummary]:
        for participant in participants:
            if participant.user_id != current_user_id:
                return ChatUserSummary(id=participant.user_id, name=participant.name or "")
        return None

    @staticmethod
    def _user_name(user: Optional[User]) -> Optional[str]:
        if not user:
            return None
        return f"{user.first_names} {user.last_name}".strip()

    def _user_summary(self, user: User) -> ChatUserSummary:
        return ChatUserSummary(id=user.id, name=self._user_name(user) or "")
