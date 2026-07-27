from datetime import datetime, timedelta

import pytest

# Mark all tests in this file as skipped - these chat tests are deprecated
# Use chats_v2 tests instead
pytestmark = pytest.mark.skip(reason="Deprecated chat tests - use chats_v2 tests instead")

from fastapi.testclient import TestClient

from Backend.tests.chat.http_utils import register_and_login, seed_direct_chat, seed_event_chat


def test_list_rooms_returns_summaries_with_unread_counts(client: TestClient, auth_user):
    other = register_and_login(client)
    event, event_room, event_messages = seed_event_chat(
        organizer_id=auth_user["user"]["id"],
        participant_id=other["user"]["id"],
        message_specs=[
            (other["user"]["id"], "group hello", datetime.utcnow() - timedelta(minutes=1)),
            (other["user"]["id"], "group update", datetime.utcnow()),
        ],
    )
    direct_room, direct_messages = seed_direct_chat(
        auth_user["user"]["id"],
        other["user"]["id"],
        context=f"event:{event.id}",
        message_specs=[(other["user"]["id"], "dm ping", datetime.utcnow())],
    )

    response = client.get("/api/chat/rooms", headers=auth_user["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload.get("meta", {}).get("total") == 2
    rooms = {room["id"]: room for room in payload["data"]}
    assert event_room.id in rooms
    assert direct_room.id in rooms

    event_payload = rooms[event_room.id]
    assert event_payload["room_type"] == "event_group"
    assert event_payload["event_id"] == event.id
    assert event_payload["unread_count"] == len(event_messages)
    assert event_payload["last_message"]["content"] == "group update"
    assert event_payload["last_message"]["sender_id"] == other["user"]["id"]
    participant_roles = {p["user_id"]: p["role"] for p in event_payload["participants"]}
    assert participant_roles[auth_user["user"]["id"]] == "owner"
    assert participant_roles[other["user"]["id"]] == "participant"

    direct_payload = rooms[direct_room.id]
    assert direct_payload["room_type"] == "direct"
    assert direct_payload.get("context") == f"event:{event.id}"
    assert direct_payload["unread_count"] == len(direct_messages)
    assert direct_payload["last_message"]["content"] == "dm ping"
    assert direct_payload["last_message"]["sender_id"] == other["user"]["id"]
    assert direct_payload["other_user"]["id"] == other["user"]["id"]
    assert "Fulda" in direct_payload["other_user"]["name"]
    direct_participants = {p["user_id"] for p in direct_payload["participants"]}
    assert {auth_user["user"]["id"], other["user"]["id"]} == direct_participants


def test_unread_counts_and_mark_read_flow(client: TestClient, auth_user):
    other = register_and_login(client)
    direct_room, messages = seed_direct_chat(
        auth_user["user"]["id"],
        other["user"]["id"],
        message_specs=[
            (other["user"]["id"], "first message", datetime.utcnow() - timedelta(minutes=1)),
            (other["user"]["id"], "second message", datetime.utcnow()),
        ],
    )

    unread = client.get("/api/chat/unread", headers=auth_user["headers"])
    assert unread.status_code == 200
    unread_payload = unread.json()
    assert unread_payload["success"] is True
    room_unread = {entry["room_id"]: entry["unread"] for entry in unread_payload["data"]["rooms"]}
    assert room_unread[direct_room.id] == len(messages)
    assert unread_payload["data"]["total"] == len(messages)

    mark_read = client.post(
        f"/api/chat/rooms/{direct_room.id}/read",
        json={"message_id": messages[-1].id},
        headers=auth_user["headers"],
    )
    assert mark_read.status_code == 200
    mark_payload = mark_read.json()
    assert mark_payload["success"] is True
    assert mark_payload["data"]["room_id"] == direct_room.id
    assert mark_payload["data"]["unread"] == 0
    assert mark_payload["data"]["last_read_message_id"] == messages[-1].id

    unread_after = client.get("/api/chat/unread", headers=auth_user["headers"])
    room_unread_after = {entry["room_id"]: entry["unread"] for entry in unread_after.json()["data"]["rooms"]}
    assert room_unread_after.get(direct_room.id, 0) == 0
