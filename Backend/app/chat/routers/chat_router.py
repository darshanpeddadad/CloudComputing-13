from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.chat.controllers import chat_loop, join_direct_room, join_event_room
from app.chat.guards import ensure_authenticated, ensure_direct_chat_access, ensure_event_room_access
from app.chat.infrastructure.connection_manager import chat_manager
from app.chat.models import ChatRoomType
from app.chat.services import ChatService
from app.chat.dependencies import get_chat_service


from websockets.exceptions import ConnectionClosed

def get_chat_router() -> APIRouter:
    router = APIRouter(prefix="/ws", tags=["chat"])

    @router.websocket("/events/{event_id}/group")
    async def event_group_chat(websocket: WebSocket, event_id: str, service: ChatService = Depends(get_chat_service)):
        session = service.session
        user = await ensure_authenticated(websocket, session)
        event = await ensure_event_room_access(websocket, service, event_id, user)
        room = await join_event_room(websocket, session, service, user, event)

        try:
            await chat_loop(
                websocket,
                session,
                service,
                room=room,
                room_type=ChatRoomType.EVENT_GROUP,
                user=user,
            )
        except (WebSocketDisconnect, ConnectionClosed):
            chat_manager.disconnect(room.id, websocket)

    @router.websocket("/direct/{target_user_id}")
    async def direct_chat(
        websocket: WebSocket,
        target_user_id: str,
        event_id: Optional[str] = None,
        service: ChatService = Depends(get_chat_service),
    ):
        session = service.session
        user = await ensure_authenticated(websocket, session)
        event, target, context = await ensure_direct_chat_access(
            websocket,
            service,
            event_id=event_id,
            target_id=target_user_id,
            user=user,
        )
        room = await join_direct_room(
            websocket,
            session,
            service,
            user=user,
            target=target,
            context=context,
            event=event,
        )

        try:
            await chat_loop(
                websocket,
                session,
                service,
                room=room,
                room_type=ChatRoomType.DIRECT,
                user=user,
                context=context,
            )
        except (WebSocketDisconnect, ConnectionClosed):
            chat_manager.disconnect(room.id, websocket)

    return router
