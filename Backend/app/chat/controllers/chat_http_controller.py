from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.chat.dependencies import get_chat_service
from app.chat.schemas import ChatMessageResponse, ChatRoomSummary, MarkReadResponse, UnreadSummary
from app.chat.services import ChatService


def get_chat_http_controller(
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> "ChatHttpController":
    return ChatHttpController(service, current_user)


class ChatHttpController:
    """Coordinates HTTP chat endpoints."""

    def __init__(self, service: ChatService, current_user: User):
        self._service = service
        self._current_user = current_user

    @property
    def user(self) -> User:
        return self._current_user

    async def list_rooms(self) -> tuple[List[ChatRoomSummary], dict]:
        rooms = await self._service.list_room_summaries(self.user.id)
        meta = {"total": len(rooms)}
        return rooms, meta

    async def list_messages(
        self,
        room_id: str,
        *,
        limit: int,
        before: Optional[datetime],
    ) -> tuple[List[ChatMessageResponse], dict]:
        participant = await self._service.get_participant(room_id, self.user.id)
        if not participant:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed in this room.")

        messages, total, has_more, next_before = await self._service.list_messages(
            room_id, limit=limit, before=before
        )
        meta = {
            "total": total,
            "has_more": has_more,
            "next_before": next_before.isoformat() if next_before else None,
        }
        return [self._service.to_message_response(msg) for msg in messages], meta

    async def unread_summary(self) -> UnreadSummary:
        return await self._service.unread_summary(self.user.id)

    async def mark_read(self, room_id: str, message_id: str) -> MarkReadResponse:
        participant = await self._service.get_participant(room_id, self.user.id)
        if not participant:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed in this room.")

        result = await self._service.mark_room_read(room_id, self.user.id, message_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found in room.")
        return result
