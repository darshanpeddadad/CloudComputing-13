from __future__ import annotations

from typing import Any

import socketio

from app.chats_v2.infrastructure.event_group_state import EventGroupRoomState
from app.chats_v2.services.event_group_chat_service import EventGroupChatError, EventGroupChatService
from app.database import SessionLocal
from app.chat.services.chat_service import ChatService
from app.chat.models import ChatParticipantRole
from app.auth.models import User, Role
from app.tickets.models import Ticket
from app.rewards.models import EventParticipation
from sqlalchemy import select
from sqlalchemy.orm import selectinload

MAX_MESSAGE_LENGTH = 4096
event_group_state = EventGroupRoomState()


def _normalize_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


async def _emit_error(server: socketio.AsyncServer, sid: str, message: str) -> None:
    await server.emit("event_group:error", {"message": message}, to=sid)


async def _broadcast_participants(
    server: socketio.AsyncServer, room_id: str, event_id: str | None
) -> None:
    # Get participants from in-memory state (active socket connections)
    state_participants = event_group_state.participants_payload(room_id)
    state_dict = {p["user_id"]: p["role"] for p in state_participants}
    
    # Merge with database to get correct roles and include auto-added participants
    # Always include all database participants (organizer, admins, ticket holders)
    # Active socket connections get their roles from database
    if event_id:
        async with SessionLocal() as db_session:
            try:
                from app.chat.models import ChatRoom, ChatParticipant
                room_stmt = select(ChatRoom).where(
                    ChatRoom.event_id == event_id,
                    ChatRoom.room_type == "event_group"
                )
                room = (await db_session.scalars(room_stmt)).first()
                if room:
                    participants_stmt = select(ChatParticipant).where(ChatParticipant.room_id == room.id)
                    db_participants = (await db_session.scalars(participants_stmt)).all()
                    db_dict = {p.user_id: p.role for p in db_participants}
                    
                    # Start with all database participants
                    state_dict = db_dict.copy()
                    
                    # Update roles for active socket connections (they might have different roles)
                    # But keep all database participants in the list
                    for user_id in list(state_dict.keys()):
                        if user_id in db_dict:
                            state_dict[user_id] = db_dict[user_id]
            except Exception:
                # If database lookup fails, just use state participants
                pass
    
    # Convert to list format
    participants = [
        {"user_id": user_id, "role": role}
        for user_id, role in state_dict.items()
    ]
    participants.sort(key=lambda item: (item["role"] != ChatParticipantRole.OWNER.value, item["user_id"]))
    
    # Use database room_id if available, otherwise use socket room_id
    database_room_id = event_group_state.database_room_id_for_room(room_id)
    emitted_room_id = database_room_id or room_id
    
    await server.emit(
        "event_group:participants",
        {"room_id": emitted_room_id, "event_id": event_id, "participants": participants},
        room=room_id,  # Still use socket room_id for Socket.IO room targeting
    )


def _role_priority(role: str) -> int:
    return 2 if role == ChatParticipantRole.OWNER.value else 1


async def _emit_event_end(server: socketio.AsyncServer, room_id: str, event_id: str | None) -> None:
    await server.emit(
        "event_group:ended",
        {"room_id": room_id, "event_id": event_id, "message": "Event has ended"},
        room=room_id,
    )


async def _disconnect_room(server: socketio.AsyncServer, room_id: str) -> None:
    for sid in event_group_state.sids_for_room(room_id):
        await server.leave_room(sid, room_id)
        await server.disconnect(sid)


async def _handle_group_join(server: socketio.AsyncServer, sid: str, data: Any) -> None:
    session = await server.get_session(sid) or {}
    user_id = session.get("user_id")
    if not user_id:
        await _emit_error(server, sid, "Unauthorized")
        return

    event_id = _normalize_str(data.get("event_id")) if isinstance(data, dict) else ""
    if not event_id:
        await _emit_error(server, sid, "event_id is required")
        return

    async with SessionLocal() as db_session:
        service = EventGroupChatService(db_session)
        try:
            join_result = await service.prepare_group_join(user_id, event_id)
        except EventGroupChatError as exc:
            await _emit_error(server, sid, str(exc))
            return

        # Persist room and ensure current user is added
        # Note: Organizer and admins are auto-added when event is approved (in EventService.approve_event)
        # Ticket holders are auto-added when tickets are purchased (to be implemented)
        database_room_id = None
        try:
            from app.events.models import Event
            from app.auth.utils.auth_checks import is_admin

            event = await service.get_event(event_id)
            user = await db_session.get(User, user_id)
            if event and user:
                chat_service = ChatService(db_session)
                # Room should already exist (created when event was approved)
                # But ensure it exists in case it wasn't created
                room = await chat_service.ensure_event_group_room(event, user)
                
                # Ensure organizer is added (in case room was created before approval flow)
                if event.organizer_id:
                    organizer = event.organizer if hasattr(event, 'organizer') and event.organizer else await db_session.get(User, event.organizer_id)
                    if organizer:
                        await chat_service.ensure_participant(room, organizer, ChatParticipantRole.OWNER)
                
                # Ensure current user is added - check database first for existing role
                from app.chat.models import ChatParticipant
                existing_participant_stmt = select(ChatParticipant).where(
                    ChatParticipant.room_id == room.id,
                    ChatParticipant.user_id == user_id
                )
                existing_participant = (await db_session.scalars(existing_participant_stmt)).first()
                
                if existing_participant:
                    # Use existing role from database (preserves role on reconnection)
                    # But ensure admins and organizers are owners
                    if is_admin(user) or event.organizer_id == user.id:
                        role = ChatParticipantRole.OWNER
                    else:
                        role = ChatParticipantRole(existing_participant.role)
                else:
                    # New participant - determine role
                    role = ChatParticipantRole.OWNER if (is_admin(user) or event.organizer_id == user.id) else ChatParticipantRole.PARTICIPANT
                
                await chat_service.ensure_participant(room, user, role)
                await chat_service.densify_admin_as_owner(room, user)
                
                # Get final role from database after ensure_participant
                final_participant_stmt = select(ChatParticipant).where(
                    ChatParticipant.room_id == room.id,
                    ChatParticipant.user_id == user_id
                )
                final_participant = (await db_session.scalars(final_participant_stmt)).first()
                if final_participant:
                    join_result.role = final_participant.role
                
                await db_session.commit()
                # Store database room ID in state
                database_room_id = room.id
        except Exception:
            # Don't block socket flow if persistence fails
            pass

    await server.enter_room(sid, join_result.room_id)
    event_group_state.track_join(
        sid=sid,
        room_id=join_result.room_id,
        event_id=join_result.event_id,
        user_id=user_id,
        role=join_result.role,
        database_room_id=database_room_id,
    )

    # Use database room ID if available, otherwise use socket room ID
    emitted_room_id = database_room_id or join_result.room_id
    await server.emit(
        "event_group:joined",
        {
            "room_id": emitted_room_id,
            "event_id": join_result.event_id,
            "role": join_result.role,
        },
        to=sid,
    )
    await _broadcast_participants(server, join_result.room_id, join_result.event_id)


async def _handle_group_message(server: socketio.AsyncServer, sid: str, data: Any) -> None:
    session = await server.get_session(sid) or {}
    sender_id = session.get("user_id")
    if not sender_id:
        await _emit_error(server, sid, "Unauthorized")
        return

    room_id_raw = _normalize_str(data.get("room_id")) if isinstance(data, dict) else ""
    content = _normalize_str(data.get("content") or data.get("message") if isinstance(data, dict) else "")

    if not room_id_raw:
        await _emit_error(server, sid, "room_id is required")
        return
    if not content:
        await _emit_error(server, sid, "Message content is required")
        return
    if len(content) > MAX_MESSAGE_LENGTH:
        await _emit_error(server, sid, f"Message too long (max {MAX_MESSAGE_LENGTH} characters)")
        return
    
    # Handle both database room_id and socket room_id
    # First try to find socket room_id from database room_id
    socket_room_id = None
    event_id = None
    database_room_id = None
    
    # Check if room_id_raw is a database room_id (UUID format)
    if room_id_raw.startswith("event:group:"):
        # It's a socket room_id
        socket_room_id = room_id_raw
        event_id = event_group_state.event_id_for_room(socket_room_id)
        database_room_id = event_group_state.database_room_id_for_room(socket_room_id)
    else:
        # It might be a database room_id - look it up
        async with SessionLocal() as db_session:
            try:
                from app.chat.models import ChatRoom
                room = await db_session.get(ChatRoom, room_id_raw)
                if room and room.room_type == "event_group" and room.event_id:
                    database_room_id = room_id_raw
                    event_id = room.event_id
                    socket_room_id = f"event:group:{event_id}"
                    # Verify user is a member of the socket room
                    if not event_group_state.is_member(sid, socket_room_id):
                        await _emit_error(server, sid, "Join the room before sending messages")
                        return
                else:
                    await _emit_error(server, sid, "Invalid room_id")
                    return
            except Exception:
                await _emit_error(server, sid, "Invalid room_id")
                return
    
    if not socket_room_id or not event_group_state.is_member(sid, socket_room_id):
        await _emit_error(server, sid, "Join the room before sending messages")
        return
    sent_at = None
    message_id = None
    
    if event_id:
        async with SessionLocal() as db_session:
            service = EventGroupChatService(db_session)
            event = await service.get_event(event_id)
            if not event or service.event_is_over(event):
                await _emit_event_end(server, room_id, event_id)
                await _disconnect_room(server, room_id)
                return
            
            # Persist message
            try:
                from app.chat.models import ChatRoom
                chat_service = ChatService(db_session)
                
                # Get the room by database_room_id or event_id
                if database_room_id:
                    room = await db_session.get(ChatRoom, database_room_id)
                else:
                    room_stmt = select(ChatRoom).where(
                        ChatRoom.event_id == event_id,
                        ChatRoom.room_type == "event_group"
                    )
                    room = (await db_session.scalars(room_stmt)).first()
                
                if room:
                    sender = await db_session.get(User, sender_id)
                    if sender:
                        message_obj = await chat_service.save_message(room, sender, content)
                        await db_session.commit()
                        sent_at = message_obj.sent_at.isoformat()
                        message_id = message_obj.id
            except Exception:
                # Don't block socket flow if persistence fails
                pass

    # Use database room_id in payload if available, otherwise use socket room_id
    emitted_room_id = database_room_id or room_id
    
    payload = {
        "room_id": emitted_room_id,
        "room_type": "event_group",
        "event_id": event_id,
        "sender_id": sender_id,
        "content": content,
        **({"sent_at": sent_at} if sent_at else {}),
        **({"id": message_id} if message_id else {}),
    }
    await server.emit("event_group:message", payload, room=socket_room_id)  # Use socket room_id for Socket.IO room targeting


async def _handle_group_leave(server: socketio.AsyncServer, sid: str, data: Any) -> None:
    session = await server.get_session(sid) or {}
    user_id = session.get("user_id")
    if not user_id:
        await _emit_error(server, sid, "Unauthorized")
        return

    room_id = _normalize_str(data.get("room_id")) if isinstance(data, dict) else ""
    event_id = _normalize_str(data.get("event_id")) if isinstance(data, dict) else ""

    if not room_id and event_id:
        room_id = f"event:group:{event_id}"
    if not room_id:
        await _emit_error(server, sid, "room_id is required")
        return

    sids = event_group_state.remove_user(room_id, user_id)
    if not sids and not event_group_state.is_member(sid, room_id):
        await _emit_error(server, sid, "Not joined to room")
        return

    for target_sid in sids or [sid]:
        await server.leave_room(target_sid, room_id)
    await _broadcast_participants(server, room_id, event_group_state.event_id_for_room(room_id))


async def handle_group_disconnect(server: socketio.AsyncServer, sid: str) -> None:
    result = event_group_state.remove_sid(sid)
    if result and result[2]:
        room_id, event_id, _ = result
        await _broadcast_participants(server, room_id, event_id)


def register_event_group_events(server: socketio.AsyncServer) -> None:
    """Register Socket.IO event handlers for event group chat."""

    @server.on("event_group:join")
    async def _join(sid, data):
        await _handle_group_join(server, sid, data)

    @server.on("event_group:message")
    async def _message(sid, data):
        await _handle_group_message(server, sid, data)

    @server.on("event_group:leave")
    async def _leave(sid, data):
        await _handle_group_leave(server, sid, data)
