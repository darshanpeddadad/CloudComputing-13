import pytest
import socketio
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.chat.models import ChatMessage, ChatRoom, ChatRoomType
from app.database import SessionLocal

from Backend.tests.chats_v2.utils import (
    DirectSocketClient,
    add_participation,
    create_event,
    promote_to_admin,
    register_and_login,
)


@pytest.mark.asyncio
async def test_direct_v2_missing_token_rejected(socketio_url: str):
    client = socketio.AsyncClient()
    with pytest.raises(socketio.exceptions.ConnectionError):
        await client.connect(
            socketio_url,
            socketio_path="/socket.io",
            transports=["websocket"],
        )


@pytest.mark.asyncio
async def test_direct_v2_user_to_admin_dm_broadcasts_to_both(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    admin = register_and_login(client)
    user = register_and_login(client)
    await promote_to_admin(admin["user"]["id"])

    admin_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, admin["token"])
    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])

    await admin_socket.connect()
    await user_socket.connect()
    try:
        await admin_socket.join_direct(target_user_id=user["user"]["id"])
        await user_socket.join_direct(target_user_id=admin["user"]["id"])

        admin_joined = await admin_socket.next_joined()
        user_joined = await user_socket.next_joined()
        assert admin_joined["context"] == "admin"
        assert user_joined["context"] == "admin"
        assert admin_joined["room_id"] == user_joined["room_id"]

        await user_socket.send_message(user_joined["room_id"], "hello admin")
        admin_msg = await admin_socket.next_message()
        user_echo = await user_socket.next_message()
        assert admin_msg["content"] == "hello admin"
        assert admin_msg["context"] == "admin"
        assert user_echo["content"] == "hello admin"
        assert user_echo["context"] == "admin"
    finally:
        await admin_socket.disconnect()
        await user_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_requires_event_for_non_admin(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    user = register_and_login(client)

    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])
    await user_socket.connect()
    try:
        await user_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=None)
        error = await user_socket.next_error()
        assert "event" in error.get("message", "").lower()
    finally:
        await user_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_rejects_invalid_token_on_connect(socketio_url: str):
    invalid_socket = socketio.AsyncClient()
    with pytest.raises(socketio.exceptions.ConnectionError):
        await invalid_socket.connect(
            socketio_url,
            socketio_path="/socket.io",
            transports=["websocket"],
            auth={"token": "bad-token"},
        )


@pytest.mark.asyncio
async def test_direct_v2_event_context_broadcasts_and_echoes(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    participant = register_and_login(client)
    event = await create_event(organizer["user"]["id"])
    await add_participation(event.id, participant["user"]["id"])

    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    participant_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, participant["token"])

    await org_socket.connect()
    await participant_socket.connect()
    try:
        await org_socket.join_direct(target_user_id=participant["user"]["id"], event_id=event.id)
        await participant_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=event.id)

        org_joined = await org_socket.next_joined()
        participant_joined = await participant_socket.next_joined()
        assert org_joined["room_id"] == participant_joined["room_id"]
        assert org_joined["context"] == f"event:{event.id}"
        assert participant_joined["context"] == f"event:{event.id}"

        await participant_socket.send_message(participant_joined["room_id"], "hello organizer")
        organizer_msg = await org_socket.next_message()
        participant_echo = await participant_socket.next_message()
        assert organizer_msg["content"] == "hello organizer"
        assert participant_echo["content"] == "hello organizer"
        assert organizer_msg["context"] == f"event:{event.id}"
        assert participant_echo["context"] == f"event:{event.id}"
    finally:
        await org_socket.disconnect()
        await participant_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_attendee_to_organizer_rejected_when_event_ended(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    attendee = register_and_login(client)
    past_event = await create_event(organizer["user"]["id"], ends_in_past=True)
    await add_participation(past_event.id, attendee["user"]["id"])

    attendee_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, attendee["token"])
    await attendee_socket.connect()
    try:
        await attendee_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=past_event.id)
        error = await attendee_socket.next_error()
        assert "ended" in error.get("message", "").lower()
    finally:
        await attendee_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_attendee_to_organizer_delivered_before_end(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    attendee = register_and_login(client)
    future_event = await create_event(organizer["user"]["id"], ends_in_past=False)
    await add_participation(future_event.id, attendee["user"]["id"])

    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    attendee_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, attendee["token"])

    await org_socket.connect()
    await attendee_socket.connect()
    try:
        await attendee_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=future_event.id)
        await org_socket.join_direct(target_user_id=attendee["user"]["id"], event_id=future_event.id)

        attendee_joined = await attendee_socket.next_joined()
        org_joined = await org_socket.next_joined()
        assert attendee_joined["room_id"] == org_joined["room_id"]
        assert attendee_joined["context"] == f"event:{future_event.id}"

        await attendee_socket.send_message(attendee_joined["room_id"], "see you soon")
        org_msg = await org_socket.next_message()
        attendee_echo = await attendee_socket.next_message()
        assert org_msg["content"] == "see you soon"
        assert attendee_echo["content"] == "see you soon"
    finally:
        await org_socket.disconnect()
        await attendee_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_organizer_can_dm_outsider_when_event_active(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    outsider = register_and_login(client)
    event = await create_event(organizer["user"]["id"])

    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    outsider_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, outsider["token"])
    await org_socket.connect()
    await outsider_socket.connect()
    try:
        await org_socket.join_direct(target_user_id=outsider["user"]["id"], event_id=event.id)
        await outsider_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=event.id)

        org_joined = await org_socket.next_joined()
        outsider_joined = await outsider_socket.next_joined()
        assert org_joined["room_id"] == outsider_joined["room_id"]

        await org_socket.send_message(org_joined["room_id"], "hello outsider")
        outsider_msg = await outsider_socket.next_message()
        org_echo = await org_socket.next_message()
        assert outsider_msg["content"] == "hello outsider"
        assert org_echo["content"] == "hello outsider"

        async with SessionLocal() as session:
            message = (
                await session.scalars(
                    select(ChatMessage).where(ChatMessage.sender_id == organizer["user"]["id"], ChatMessage.content == "hello outsider")
                )
            ).first()
            assert message is not None
            room = await session.get(ChatRoom, message.room_id)
            assert room is not None
            assert room.room_type == ChatRoomType.DIRECT.value
            meta = room.metadata_json or {}
            assert meta.get("event_id") == event.id
            assert meta.get("context") == f"event:{event.id}"
    finally:
        await org_socket.disconnect()
        await outsider_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_outsider_to_organizer_before_and_after_event(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    outsider = register_and_login(client)
    future_event = await create_event(organizer["user"]["id"], ends_in_past=False)
    past_event = await create_event(organizer["user"]["id"], ends_in_past=True)

    # Future event: allowed
    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    outsider_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, outsider["token"])
    await org_socket.connect()
    await outsider_socket.connect()
    try:
        await outsider_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=future_event.id)
        await org_socket.join_direct(target_user_id=outsider["user"]["id"], event_id=future_event.id)

        outsider_joined = await outsider_socket.next_joined()
        org_joined = await org_socket.next_joined()
        assert outsider_joined["room_id"] == org_joined["room_id"]

        await outsider_socket.send_message(outsider_joined["room_id"], "hi organizer")
        org_msg = await org_socket.next_message()
        outsider_echo = await outsider_socket.next_message()
        assert org_msg["content"] == "hi organizer"
        assert outsider_echo["content"] == "hi organizer"
    finally:
        await org_socket.disconnect()
        await outsider_socket.disconnect()

    # Past event: rejected
    late_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, outsider["token"])
    await late_socket.connect()
    try:
        await late_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=past_event.id)
        error = await late_socket.next_error()
        assert "ended" in error.get("message", "").lower()
    finally:
        await late_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_organizer_cannot_dm_outsider_when_event_ended(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    outsider = register_and_login(client)
    ended_event = await create_event(organizer["user"]["id"], ends_in_past=True)

    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    await org_socket.connect()
    try:
        await org_socket.join_direct(target_user_id=outsider["user"]["id"], event_id=ended_event.id)
        error = await org_socket.next_error()
        assert "ended" in error.get("message", "").lower() or "inactive" in error.get("message", "").lower()
    finally:
        await org_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_recipient_must_exist(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    user = register_and_login(client)
    admin = register_and_login(client)
    await promote_to_admin(admin["user"]["id"])

    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])
    admin_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, admin["token"])

    await user_socket.connect()
    await admin_socket.connect()
    try:
        await user_socket.join_direct(target_user_id="missing-user", event_id=None)
        error_user = await user_socket.next_error()
        assert "recipient" in error_user.get("message", "").lower() or "not found" in error_user.get("message", "").lower()

        await admin_socket.join_direct(target_user_id="missing-user", event_id=None)
        error_admin = await admin_socket.next_error()
        assert "recipient" in error_admin.get("message", "").lower() or "not found" in error_admin.get("message", "").lower()
    finally:
        await user_socket.disconnect()
        await admin_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_organizer_dm_participant_delivers(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    organizer = register_and_login(client)
    participant = register_and_login(client)
    event = await create_event(organizer["user"]["id"])
    await add_participation(event.id, participant["user"]["id"])

    org_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, organizer["token"])
    participant_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, participant["token"])
    await org_socket.connect()
    await participant_socket.connect()
    try:
        await org_socket.join_direct(target_user_id=participant["user"]["id"], event_id=event.id)
        await participant_socket.join_direct(target_user_id=organizer["user"]["id"], event_id=event.id)

        org_joined = await org_socket.next_joined()
        participant_joined = await participant_socket.next_joined()
        assert org_joined["room_id"] == participant_joined["room_id"]

        await org_socket.send_message(org_joined["room_id"], "hi participant")
        participant_msg = await participant_socket.next_message()
        org_echo = await org_socket.next_message()
        assert participant_msg["content"] == "hi participant"
        assert org_echo["content"] == "hi participant"
    finally:
        await org_socket.disconnect()
        await participant_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_admin_dm_without_event_delivers(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    admin = register_and_login(client)
    await promote_to_admin(admin["user"]["id"])
    user = register_and_login(client)

    admin_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, admin["token"])
    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])

    await admin_socket.connect()
    await user_socket.connect()
    try:
        await admin_socket.join_direct(target_user_id=user["user"]["id"])
        await user_socket.join_direct(target_user_id=admin["user"]["id"])
        admin_joined = await admin_socket.next_joined()
        await user_socket.next_joined()

        await admin_socket.send_message(admin_joined["room_id"], "hello from admin")
        user_msg = await user_socket.next_message()
        admin_echo = await admin_socket.next_message()
        assert user_msg["content"] == "hello from admin"
        assert admin_echo["content"] == "hello from admin"
        assert user_msg["context"] == "admin"
        assert admin_echo["context"] == "admin"
    finally:
        await admin_socket.disconnect()
        await user_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_empty_message_returns_error_no_broadcast(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    admin = register_and_login(client)
    await promote_to_admin(admin["user"]["id"])
    user = register_and_login(client)

    admin_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, admin["token"])
    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])

    await admin_socket.connect()
    await user_socket.connect()
    try:
        await admin_socket.join_direct(target_user_id=user["user"]["id"])
        await user_socket.join_direct(target_user_id=admin["user"]["id"])
        admin_joined = await admin_socket.next_joined()
        await user_socket.next_joined()

        await admin_socket.send_message(admin_joined["room_id"], "   ")
        error = await admin_socket.next_error()
        assert "content" in error.get("message", "").lower()
        assert await user_socket.poll_message() is None
    finally:
        await admin_socket.disconnect()
        await user_socket.disconnect()


@pytest.mark.asyncio
async def test_direct_v2_large_message_rejected_no_broadcast(
    client: TestClient,
    socketio_url: str,
    direct_socket_client_factory,
):
    admin = register_and_login(client)
    await promote_to_admin(admin["user"]["id"])
    user = register_and_login(client)

    admin_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, admin["token"])
    user_socket: DirectSocketClient = direct_socket_client_factory(socketio_url, user["token"])
    big_message = "x" * 6000

    await admin_socket.connect()
    await user_socket.connect()
    try:
        await admin_socket.join_direct(target_user_id=user["user"]["id"])
        await user_socket.join_direct(target_user_id=admin["user"]["id"])
        admin_joined = await admin_socket.next_joined()
        await user_socket.next_joined()

        await admin_socket.send_message(admin_joined["room_id"], big_message)
        error = await admin_socket.next_error()
        assert "long" in error.get("message", "").lower() or "length" in error.get("message", "").lower()
        assert await user_socket.poll_message() is None
    finally:
        await admin_socket.disconnect()
        await user_socket.disconnect()
