from __future__ import annotations

from typing import Optional, Tuple

from fastapi import WebSocket, status

from app.auth.models import User
from app.auth.utils import is_admin, user_from_token
from app.chat.services import ChatService
from app.chat.utils.websocket_utils import reject
from app.events.models import Event


async def ensure_authenticated(websocket: WebSocket, session) -> User:
    """Return current user or reject if unauthenticated."""
    token = websocket.headers.get("Authorization")
    if not token:
        raw_token = websocket.query_params.get("token")
        if raw_token:
            token = f"Bearer {raw_token}"
    
    user = await user_from_token(session, token)
    if not user:
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Unauthorized")
    return user


async def ensure_event_room_access(
    websocket: WebSocket,
    service: ChatService,
    event_id: str,
    user: User,
) -> Event:
    """Validate event existence and membership for group chat."""
    event = await service.get_event(event_id)
    if not event:
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Event not found")

    is_participant = await service.is_event_participant(event_id, user.id)
    is_organizer = user.id == event.organizer_id
    if not (is_participant or is_organizer or is_admin(user)):
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Not allowed in this chat")
    return event


async def ensure_direct_chat_access(
    websocket: WebSocket,
    service: ChatService,
    *,
    event_id: Optional[str],
    target_id: str,
    user: User,
) -> Tuple[Optional[Event], User, str]:
    """
    Validate direct chat access and return (event, target, context).
    Context is 'admin' for admin DMs, or 'event:{id}' for organizer/participant chats.
    """
    event, target = await service.event_and_target_for_direct(event_id, target_id)
    if not target:
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Recipient not found")

    # Admin DMs don't require event context
    if is_admin(target) or is_admin(user):
        return None, target, "admin"

    if not event:
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Missing event context")

    user_is_organizer = user.id == event.organizer_id
    target_is_organizer = target.id == event.organizer_id
    if not (user_is_organizer or target_is_organizer):
        await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Organizer only")

    if target_is_organizer:
        # Non-participants can initiate to the organizer, but cannot do so after the event ends.
        if service.event_is_over(event) and not user_is_organizer:
            await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Event has ended; direct chat disabled")
        return event, target, f"event:{event.id}"

    # Organizer is initiating to someone else.
    # Organizer can only DM participants, unless a room already exists (indicating target initiated first).
    if user_is_organizer:
        target_is_participant = await service.is_event_participant(event.id, target.id)
        if not target_is_participant:
            # Check if room already exists (target initiated first)
            context = f"event:{event.id}"
            room_exists = await service.direct_room_exists(user.id, target.id, context)
            if not room_exists:
                await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Target not a participant")
        return event, target, f"event:{event.id}"

    # This should not be reached due to the check above, but keep for safety
    await reject(websocket, status.WS_1008_POLICY_VIOLATION, "Not allowed")
    return event, target, f"event:{event.id}"  # Never reached

