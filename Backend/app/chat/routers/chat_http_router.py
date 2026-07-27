from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.chat.controllers import ChatHttpController, get_chat_http_controller
from app.chat.presentation import MarkReadRequest
from app.common import success_response


def get_chat_http_router() -> APIRouter:
    router = APIRouter(prefix="/api/chat", tags=["chat"])

    @router.get("/rooms")
    async def list_rooms(controller: ChatHttpController = Depends(get_chat_http_controller)):
        rooms, meta = await controller.list_rooms()
        return success_response([room.model_dump() for room in rooms], meta=meta)

    @router.get("/rooms/{room_id}/messages")
    async def list_messages(
        room_id: str,
        limit: int = Query(20, ge=1, le=50),
        before: Optional[datetime] = Query(None),
        controller: ChatHttpController = Depends(get_chat_http_controller),
    ):
        messages, meta = await controller.list_messages(room_id, limit=limit, before=before)
        return success_response([message.model_dump() for message in messages], meta=meta)

    @router.get("/unread")
    async def unread_summary(controller: ChatHttpController = Depends(get_chat_http_controller)):
        summary = await controller.unread_summary()
        return success_response(summary)

    @router.post("/rooms/{room_id}/read")
    async def mark_read(
        room_id: str,
        payload: MarkReadRequest,
        controller: ChatHttpController = Depends(get_chat_http_controller),
    ):
        result = await controller.mark_read(room_id, payload.message_id)
        return success_response(result)

    return router
