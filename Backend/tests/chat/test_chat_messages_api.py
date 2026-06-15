from datetime import datetime, timedelta

import pytest

# Mark all tests in this file as skipped - these chat tests are deprecated
# Use chats_v2 tests instead
pytestmark = pytest.mark.skip(reason="Deprecated chat tests - use chats_v2 tests instead")

from fastapi.testclient import TestClient

from Backend.tests.chat.http_utils import register_and_login, seed_direct_chat


def test_messages_endpoint_supports_limit_and_before_filter(client: TestClient, auth_user):
    other = register_and_login(client)
    base = datetime.utcnow()
    message_specs = [
        (other["user"]["id"], "first", base - timedelta(minutes=2)),
        (auth_user["user"]["id"], "second", base - timedelta(minutes=1)),
        (other["user"]["id"], "third", base),
    ]
    room, messages = seed_direct_chat(
        auth_user["user"]["id"],
        other["user"]["id"],
        message_specs=message_specs,
    )

    response = client.get(f"/api/chat/rooms/{room.id}/messages?limit=2", headers=auth_user["headers"])
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload.get("meta", {}).get("total") == len(message_specs)
    assert payload["meta"].get("has_more") is True
    assert payload["meta"].get("next_before")
    contents = [msg["content"] for msg in payload["data"]]
    assert contents == ["third", "second"]
    senders = [msg["sender"]["id"] for msg in payload["data"]]
    assert senders == [other["user"]["id"], auth_user["user"]["id"]]
    assert payload["data"][0]["sender"]["name"]

    before_ts = messages[1].sent_at.isoformat()
    older_response = client.get(
        f"/api/chat/rooms/{room.id}/messages?before={before_ts}&limit=5",
        headers=auth_user["headers"],
    )
    assert older_response.status_code == 200
    older_contents = [msg["content"] for msg in older_response.json()["data"]]
    assert older_contents == ["first"]
    assert older_response.json()["meta"].get("has_more") is False


def test_non_participant_cannot_access_messages(client: TestClient, auth_user):
    other = register_and_login(client)
    outsider = register_and_login(client)
    room, _ = seed_direct_chat(auth_user["user"]["id"], other["user"]["id"])

    response = client.get(f"/api/chat/rooms/{room.id}/messages", headers=outsider["headers"])
    assert response.status_code in (401, 403)


def test_messages_endpoint_requires_auth(client: TestClient, auth_user):
    other = register_and_login(client)
    room, _ = seed_direct_chat(auth_user["user"]["id"], other["user"]["id"])

    response = client.get(f"/api/chat/rooms/{room.id}/messages")
    assert response.status_code == 401
