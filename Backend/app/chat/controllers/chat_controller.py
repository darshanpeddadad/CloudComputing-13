from __future__ import annotations

from typing import Optional

from app.auth.models import User
from app.auth.utils import is_admin
from app.chat.infrastructure.connection_manager import chat_manager
from app.chat.models import ChatParticipantRole, ChatRoom, ChatRoomType
from app.chat.services import ChatService
from app.chat.utils.websocket_utils import error_payload
from app.events.models import Event


async def join_event_room(
    websocket,
    session,
    service: ChatService,
    user: User,
    event: Event,
) -> ChatRoom:
    """Create/prepare event room, ensure membership/roles, connect, and send participant list."""
    room = await service.ensure_event_group_room(event, user)
    await service.sync_event_room_members(room, event)
    role = ChatParticipantRole.OWNER if (user.id == event.organizer_id or is_admin(user)) else ChatParticipantRole.PARTICIPANT
    await service.ensure_participant(room, user, role)
    await service.densify_admin_as_owner(room, user)
    await session.commit()

    await chat_manager.connect(room.id, websocket)
    participants_payload = await service.list_participants_payload(room.id)
    await chat_manager.send_personal_message(
        websocket,
        {"type": "participants", "room_id": room.id, "participants": participants_payload},
    )
    return room


async def join_direct_room(
    websocket,
    session,
    service: ChatService,
    *,
    user: User,
    target: User,
    context: str,
    event: Optional[Event],
) -> ChatRoom:
    """Create/prepare direct room, ensure membership/roles, connect, and send participant list."""
    event_id_value = event.id if event else None
    event_organizer_id = event.organizer_id if event else None

    room = await service.get_or_create_direct_room(
        user,
        target,
        context,
        metadata_json={"context": context, "event_id": event_id_value, "target_user_id": target.id},
    )
    target_role = (
        ChatParticipantRole.OWNER
        if (is_admin(target) or (event_organizer_id and target.id == event_organizer_id))
        else ChatParticipantRole.PARTICIPANT
    )
    await service.ensure_participant(room, target, target_role)
    await service.ensure_participant(room, user, ChatParticipantRole.PARTICIPANT)
    await service.densify_admin_as_owner(room, user)
    await session.commit()

    await chat_manager.connect(room.id, websocket)
    participants_payload = await service.list_participants_payload(room.id)
    await chat_manager.send_personal_message(
        websocket,
        {
            "type": "participants",
            "room_id": room.id,
            "participants": participants_payload,
            "context": context,
        },
    )
    return room


async def chat_loop(
    websocket,
    session,
    service: ChatService,
    *,
    room: ChatRoom,
    room_type: ChatRoomType,
    user: User,
    context: Optional[str] = None,
):
    """Receive messages, persist, and broadcast within a room."""
    while True:
        payload = await websocket.receive_json()
        content = str(payload.get("content") or payload.get("message") or "").strip()
        if not content:
            await chat_manager.send_personal_message(websocket, error_payload("Message content is required."))
            continue
        message = await service.save_message(room, user, content)
        await session.commit()
        await chat_manager.broadcast(
            room.id,
            {
                "type": "message",
                "room_type": room_type.value,
                "room_id": room.id,
                "sender_id": user.id,
                "content": content,
                "sent_at": message.sent_at.isoformat(),
                **({"context": context} if context else {}),
            },
        )

