import asyncio
import uuid
from datetime import date, datetime, time, timedelta

import pytest

# Mark all tests in this file as skipped - these websocket tests are deprecated
# Use chats_v2 tests instead
pytestmark = pytest.mark.skip(reason="Deprecated websocket tests - use chats_v2 tests instead")

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.auth.models import Role, User
from app.database import SessionLocal
from app.events.models import Event, EventCategory, EventStatus
from app.rewards.models import EventParticipation, ParticipationStatus
from Backend.tests.auth.utils import auth_url, registration_payload


def _register_and_login(client: TestClient) -> dict:
    registration = registration_payload()
    password = registration["password"]
    register_response = client.post(auth_url("/register"), json=registration)
    assert register_response.status_code == 201

    login_response = client.post(
        auth_url("/login"),
        json={"email": registration["email"], "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    return {
        "user": data["user"],
        "token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


def _promote_to_admin(user_id: str) -> None:
    async def _run():
        async with SessionLocal() as session:
            role = await session.get(Role, "role-admin")
            if not role:
                role = Role(id="role-admin", name="admin")
                session.add(role)
                await session.flush([role])
            user = await session.get(User, user_id)
            assert user is not None
            await session.refresh(user, attribute_names=["roles"])
            if role not in user.roles:
                user.roles.append(role)
            await session.commit()

    asyncio.run(_run())


def _create_event(organizer_id: str, *, ends_in_past: bool = False) -> Event:
    async def _run():
        async with SessionLocal() as session:
            category = EventCategory(id=str(uuid.uuid4()), name=f"Categ-{uuid.uuid4().hex[:6]}")
            today = date.today()
            if ends_in_past:
                start = today - timedelta(days=1)
                end = today - timedelta(days=1)
                end_time_value = (datetime.utcnow() - timedelta(hours=1)).time()
            else:
                start = today + timedelta(days=1)
                end = today + timedelta(days=1)
                end_time_value = time(12, 0)
            event = Event(
                id=str(uuid.uuid4()),
                title="Websocket Test Event",
                description="Chat flow validation.",
                location="Fulda",
                latitude=50.55,
                longitude=9.67,
                start_date=start,
                end_date=end,
                start_time=time(10, 0),
                end_time=end_time_value,
                sos_enabled=False,
                max_attendees=50,
                status=EventStatus.APPROVED.value,
                organizer_id=organizer_id,
                category=category,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    return asyncio.run(_run())


def _add_participation(event_id: str, user_id: str) -> None:
    async def _run():
        async with SessionLocal() as session:
            participation = EventParticipation(
                id=str(uuid.uuid4()),
                event_id=event_id,
                user_id=user_id,
                status=ParticipationStatus.REGISTERED.value,
            )
            session.add(participation)
            await session.commit()

    asyncio.run(_run())


def test_event_participants_get_group_chat_with_roles(client: TestClient):
    organizer = _register_and_login(client)
    admin = _register_and_login(client)
    participant = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])

    event = _create_event(organizer["user"]["id"])
    _add_participation(event.id, participant["user"]["id"])

    with client.websocket_connect(f"/ws/events/{event.id}/group", headers=admin["headers"]) as admin_ws:
        admin_initial = admin_ws.receive_json()
        assert admin_initial["type"] == "participants"
        admin_roles = {p["user_id"]: p["role"] for p in admin_initial["participants"]}
        assert admin_roles[organizer["user"]["id"]] == "owner"
        assert admin_roles[admin["user"]["id"]] == "owner"

        with client.websocket_connect(f"/ws/events/{event.id}/group", headers=participant["headers"]) as participant_ws:
            initial = participant_ws.receive_json()
            assert initial["type"] == "participants"
            roles = {p["user_id"]: p["role"] for p in initial["participants"]}
            assert roles[organizer["user"]["id"]] == "owner"
            assert roles[admin["user"]["id"]] == "owner"
            assert roles[participant["user"]["id"]] == "participant"

            participant_ws.send_json({"content": "hello team"})
            broadcast = admin_ws.receive_json()
            assert broadcast["type"] == "message"
            assert broadcast["content"] == "hello team"
            assert broadcast["room_type"] == "event_group"
            assert broadcast["sender_id"] == participant["user"]["id"]


def test_organizer_can_join_group_chat_when_alone(client: TestClient):
    organizer = _register_and_login(client)
    event = _create_event(organizer["user"]["id"])

    with client.websocket_connect(f"/ws/events/{event.id}/group", headers=organizer["headers"]) as ws:
        initial = ws.receive_json()
        assert initial["type"] == "participants"
        roles = {p["user_id"]: p["role"] for p in initial["participants"]}
        assert roles == {organizer["user"]["id"]: "owner"}


def test_admin_join_upgrades_to_owner_in_group_chat(client: TestClient):
    organizer = _register_and_login(client)
    participant = _register_and_login(client)
    admin = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])
    event = _create_event(organizer["user"]["id"])
    _add_participation(event.id, participant["user"]["id"])

    with client.websocket_connect(f"/ws/events/{event.id}/group", headers=participant["headers"]) as participant_ws:
        participant_ws.receive_json()
        with client.websocket_connect(f"/ws/events/{event.id}/group", headers=admin["headers"]) as admin_ws:
            admin_initial = admin_ws.receive_json()
            roles = {p["user_id"]: p["role"] for p in admin_initial["participants"]}
            assert roles[organizer["user"]["id"]] == "owner"
            assert roles[admin["user"]["id"]] == "owner"
            assert roles[participant["user"]["id"]] == "participant"


def test_user_can_dm_admin_anytime(client: TestClient):
    admin = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])
    user = _register_and_login(client)

    with client.websocket_connect(f"/ws/direct/{admin['user']['id']}", headers=user["headers"]) as user_ws, client.websocket_connect(  # noqa: E501
        f"/ws/direct/{user['user']['id']}", headers=admin["headers"]
    ) as admin_ws:
        user_initial = user_ws.receive_json()
        assert user_initial["type"] == "participants"
        assert user_initial.get("context") == "admin"
        admin_initial = admin_ws.receive_json()
        assert admin_initial["type"] == "participants"
        assert admin_initial.get("context") == "admin"

        user_ws.send_json({"content": "ping admin"})
        received = admin_ws.receive_json()
        assert received["type"] == "message"
        assert received["content"] == "ping admin"
        assert received["context"] == "admin"
        assert received["sender_id"] == user["user"]["id"]


def test_dm_organizer_disallowed_after_event_end(client: TestClient):
    organizer = _register_and_login(client)
    attendee = _register_and_login(client)

    past_event = _create_event(organizer["user"]["id"], ends_in_past=True)
    _add_participation(past_event.id, attendee["user"]["id"])

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(
            f"/ws/direct/{organizer['user']['id']}?event_id={past_event.id}",
            headers=attendee["headers"],
        ):
            pass
    assert excinfo.value.code == 1008

    active_event = _create_event(organizer["user"]["id"], ends_in_past=False)
    _add_participation(active_event.id, attendee["user"]["id"])
    with client.websocket_connect(
        f"/ws/direct/{organizer['user']['id']}?event_id={active_event.id}",
        headers=attendee["headers"],
    ) as attendee_ws, client.websocket_connect(
        f"/ws/direct/{attendee['user']['id']}?event_id={active_event.id}",
        headers=organizer["headers"],
    ) as organizer_ws:
        attendee_initial = attendee_ws.receive_json()
        assert attendee_initial["type"] == "participants"
        organizer_initial = organizer_ws.receive_json()
        assert organizer_initial["type"] == "participants"
        attendee_ws.send_json({"content": "hi organizer"})
        message = organizer_ws.receive_json()
        assert message["type"] == "message"
        assert message["content"] == "hi organizer"
        assert message["context"].startswith("event:")


def test_non_participant_cannot_join_event_group_chat(client: TestClient):
    organizer = _register_and_login(client)
    outsider = _register_and_login(client)
    event = _create_event(organizer["user"]["id"])

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws/events/{event.id}/group", headers=outsider["headers"]):
            pass
    assert excinfo.value.code == 1008


def test_dm_organizer_requires_event_context_for_non_admin(client: TestClient):
    organizer = _register_and_login(client)
    user = _register_and_login(client)

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws/direct/{organizer['user']['id']}", headers=user["headers"]):
            pass
    assert excinfo.value.code == 1008


def test_organizer_cannot_dm_non_participant(client: TestClient):
    organizer = _register_and_login(client)
    outsider = _register_and_login(client)
    event = _create_event(organizer["user"]["id"])

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(
            f"/ws/direct/{outsider['user']['id']}?event_id={event.id}",
            headers=organizer["headers"],
        ):
            pass
    assert excinfo.value.code == 1008


def test_non_participant_can_initiate_dm_to_organizer_before_event_end(client: TestClient):
    organizer = _register_and_login(client)
    outsider = _register_and_login(client)
    future_event = _create_event(organizer["user"]["id"], ends_in_past=False)

    with client.websocket_connect(
        f"/ws/direct/{organizer['user']['id']}?event_id={future_event.id}",
        headers=outsider["headers"],
    ) as outsider_ws, client.websocket_connect(
        f"/ws/direct/{outsider['user']['id']}?event_id={future_event.id}",
        headers=organizer["headers"],
    ) as organizer_ws:
        outsider_initial = outsider_ws.receive_json()
        assert outsider_initial["type"] == "participants"
        organizer_initial = organizer_ws.receive_json()
        assert organizer_initial["type"] == "participants"
        outsider_ws.send_json({"content": "hey organizer"})
        msg = organizer_ws.receive_json()
        assert msg["type"] == "message"
        assert msg["content"] == "hey organizer"
        assert msg["context"].startswith("event:")


def test_non_participant_cannot_dm_organizer_after_event_end(client: TestClient):
    organizer = _register_and_login(client)
    outsider = _register_and_login(client)
    past_event = _create_event(organizer["user"]["id"], ends_in_past=True)

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(
            f"/ws/direct/{organizer['user']['id']}?event_id={past_event.id}",
            headers=outsider["headers"],
        ):
            pass
    assert excinfo.value.code == 1008


def test_dm_recipient_must_exist(client: TestClient):
    user = _register_and_login(client)
    future_event = _create_event(user["user"]["id"], ends_in_past=False)

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(
            f"/ws/direct/non-existent-user?event_id={future_event.id}",
            headers=user["headers"],
        ):
            pass
    assert excinfo.value.code == 1008


def test_cannot_connect_to_missing_event_in_group_chat(client: TestClient):
    user = _register_and_login(client)
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/events/missing-event-id/group", headers=user["headers"]):
            pass
    assert excinfo.value.code == 1008


def test_admin_dm_still_requires_existing_recipient(client: TestClient):
    admin = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/direct/non-existent-user", headers=admin["headers"]):
            pass
    assert excinfo.value.code == 1008


def test_organizer_can_initiate_dm_to_participant(client: TestClient):
    organizer = _register_and_login(client)
    participant = _register_and_login(client)
    event = _create_event(organizer["user"]["id"])
    _add_participation(event.id, participant["user"]["id"])

    with client.websocket_connect(
        f"/ws/direct/{participant['user']['id']}?event_id={event.id}",
        headers=organizer["headers"],
    ) as org_ws, client.websocket_connect(
        f"/ws/direct/{organizer['user']['id']}?event_id={event.id}",
        headers=participant["headers"],
    ) as participant_ws:
        org_ws.receive_json()
        participant_ws.receive_json()
        org_ws.send_json({"content": "hi attendee"})
        msg = participant_ws.receive_json()
        assert msg["type"] == "message"
        assert msg["content"] == "hi attendee"
        assert msg["context"].startswith("event:")


def test_admin_can_dm_without_event_context(client: TestClient):
    admin = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])
    user = _register_and_login(client)

    with client.websocket_connect(f"/ws/direct/{user['user']['id']}", headers=admin["headers"]) as admin_ws, client.websocket_connect(  # noqa: E501
        f"/ws/direct/{admin['user']['id']}", headers=user["headers"]
    ) as user_ws:
        admin_ws.receive_json()
        user_ws.receive_json()
        admin_ws.send_json({"content": "hello from admin"})
        msg = user_ws.receive_json()
        assert msg["context"] == "admin"
        assert msg["content"] == "hello from admin"


def test_empty_message_returns_error_and_no_broadcast(client: TestClient):
    admin = _register_and_login(client)
    _promote_to_admin(admin["user"]["id"])
    user = _register_and_login(client)

    with client.websocket_connect(f"/ws/direct/{user['user']['id']}", headers=admin["headers"]) as admin_ws:
        admin_ws.receive_json()
        admin_ws.send_json({"content": "   "})
        error_payload = admin_ws.receive_json()
        assert error_payload["type"] == "error"
        assert "content is required" in error_payload["message"].lower()


def test_invalid_token_rejected_on_connect(client: TestClient):
    organizer = _register_and_login(client)
    event = _create_event(organizer["user"]["id"])
    headers = {"Authorization": "Bearer invalidtoken"}

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws/events/{event.id}/group", headers=headers):
            pass
    assert excinfo.value.code == 1008

