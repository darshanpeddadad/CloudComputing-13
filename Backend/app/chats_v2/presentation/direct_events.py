from __future__ import annotations

from typing import Any

import socketio

from app.chats_v2.infrastructure.direct_room_state import DirectRoomState
from app.chats_v2.services.direct_chat_service import DirectChatError, DirectChatService
from app.database import SessionLocal
from app.auth.utils.auth_checks import is_admin
from app.chat.models import ChatParticipantRole, ChatRoom
from app.chat.services.chat_service import ChatService
from app.events.models import Event

MAX_MESSAGE_LENGTH = 4096
direct_room_state = DirectRoomState()


def _normalize_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


async def _emit_error(server: socketio.AsyncServer, sid: str, message: str) -> None:
    await server.emit("direct:error", {"message": message}, to=sid)


async def _handle_direct_join(server: socketio.AsyncServer, sid: str, data: Any) -> None:
    session = await server.get_session(sid) or {}
    user_id = session.get("user_id")
    if not user_id:
        await _emit_error(server, sid, "Unauthorized")
        return

    target_user_id = _normalize_str(data.get("target_user_id")) if isinstance(data, dict) else ""
    event_id_raw = data.get("event_id") if isinstance(data, dict) else None
    event_id = _normalize_str(event_id_raw) if event_id_raw is not None else None
    # Convert empty string to None for event_id
    if event_id == "":
        event_id = None

    if not target_user_id:
        await _emit_error(server, sid, "Recipient not found")
        return

    async with SessionLocal() as db_session:
        service = DirectChatService(db_session)
        try:
            join_result = await service.prepare_direct_join(user_id, target_user_id, event_id)
        except DirectChatError as exc:
            await _emit_error(server, sid, str(exc))
            return
        chat_room_id = None
        # Persist a chat room and participants for this direct chat
        try:
            from app.auth.models import User
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            user_stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
            user = (await db_session.scalars(user_stmt)).first()
            target_stmt = select(User).where(User.id == join_result.target_user_id).options(selectinload(User.roles))
            target = (await db_session.scalars(target_stmt)).first()
            event = await db_session.get(Event, join_result.event_id) if join_result.event_id else None
            if user and target:
                chat_service = ChatService(db_session)
                room = await chat_service.get_or_create_direct_room(
                    user,
                    target,
                    join_result.context,
                    metadata_json={
                        "context": join_result.context,
                        "event_id": join_result.event_id,
                        "target_user_id": target.id,
                    },
                )
                event_organizer_id = event.organizer_id if event else None
                target_role = (
                    ChatParticipantRole.OWNER
                    if (is_admin(target) or (event_organizer_id and target.id == event_organizer_id))
                    else ChatParticipantRole.PARTICIPANT
                )
                await chat_service.ensure_participant(room, target, target_role)
                await chat_service.ensure_participant(room, user, ChatParticipantRole.PARTICIPANT)
                await chat_service.densify_admin_as_owner(room, user)
                await db_session.commit()
                chat_room_id = room.id
        except Exception:
            # Do not block the socket flow if persistence fails; continue without chat_room_id
            # The socket connection can still work, messages just won't be persisted
            chat_room_id = None

    await server.enter_room(sid, join_result.room_id)
    direct_room_state.track_join(sid, join_result.room_id, join_result.context, chat_room_id=chat_room_id)
    await server.emit(
        "direct:joined",
        {
            "room_id": join_result.room_id,
            "context": join_result.context,
            "event_id": join_result.event_id,
            "chat_room_id": chat_room_id,
            "target_user_id": join_result.target_user_id,
        },
        to=sid,
    )


async def _handle_direct_message(server: socketio.AsyncServer, sid: str, data: Any) -> None:
    session = await server.get_session(sid) or {}
    sender_id = session.get("user_id")
    if not sender_id:
        await _emit_error(server, sid, "Unauthorized")
        return

    room_id = _normalize_str(data.get("room_id")) if isinstance(data, dict) else ""
    content = _normalize_str(data.get("content") or data.get("message") if isinstance(data, dict) else "")

    if not room_id:
        await _emit_error(server, sid, "room_id is required")
        return
    if not content:
        await _emit_error(server, sid, "Message content is required")
        return
    if len(content) > MAX_MESSAGE_LENGTH:
        await _emit_error(server, sid, f"Message too long (max {MAX_MESSAGE_LENGTH} characters)")
        return
    if not direct_room_state.is_member(sid, room_id):
        await _emit_error(server, sid, "Join the room before sending messages")
        return

    context = direct_room_state.context_for_room(room_id) or "admin"
    sent_at = None
    message_id = None
    chat_room_id = direct_room_state.chat_room_id_for_room(room_id)
    if chat_room_id:
        from app.auth.models import User

        async with SessionLocal() as db_session:
            chat_room = await db_session.get(ChatRoom, chat_room_id)
            sender = await db_session.get(User, sender_id)
            if chat_room and sender:
                chat_service = ChatService(db_session)
                message_obj = await chat_service.save_message(chat_room, sender, content)
                await db_session.commit()
                sent_at = message_obj.sent_at.isoformat()
                message_id = message_obj.id

    payload = {
        "room_id": room_id,
        "room_type": "direct",
        "sender_id": sender_id,
        "content": content,
        "context": context,
        **({"sent_at": sent_at} if sent_at else {}),
        **({"id": message_id} if message_id else {}),
    }
    await server.emit("direct:message", payload, room=room_id)


def register_direct_events(server: socketio.AsyncServer) -> None:
    """Register Socket.IO event handlers for v2 direct chat."""

    @server.on("direct:join")
    async def _join(sid, data):
        await _handle_direct_join(server, sid, data)

    @server.on("direct:message")
    async def _message(sid, data):
        await _handle_direct_message(server, sid, data)
