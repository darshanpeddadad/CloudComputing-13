import asyncio
from typing import Dict, List, Tuple

from fastapi.testclient import TestClient

from app.auth.models import User
from app.database import SessionLocal
from app.events.models import EventCategory, EventStatus
from tests.auth.utils import auth_url, detail_message, registration_payload
from tests.events.utils import create_event_for_user


def _register_user(client: TestClient) -> Dict:
    """Register and log in a user, returning auth headers and user data."""
    payload = registration_payload()
    password = payload["password"]
    reg_response = client.post(auth_url("/register"), json=payload)
    assert reg_response.status_code == 201

    login_response = client.post(
        auth_url("/login"),
        json={"email": payload["email"], "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    return {
        "user": data["user"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


def _create_events_for_user(user_id: str, category_id: str, events: List[Tuple[str, str]]) -> None:
    """Create events for a specific organizer with provided titles and statuses."""

    async def _run():
        async with SessionLocal() as session:
            organizer = await session.get(User, user_id)
            category = await session.get(EventCategory, category_id)
            assert organizer is not None, "Organizer not found when creating events"
            assert category is not None, "Category not found when creating events"

            for title, status in events:
                await create_event_for_user(
                    session,
                    organizer=organizer,
                    category=category,
                    title=title,
                    status=status,
                )
            await session.commit()

    asyncio.run(_run())


def test_organizer_can_list_only_their_events(client: TestClient, auth_user: Dict, category_factory):
    category = category_factory(name="Organizer Catalog")
    own_events = [
        ("Pending Organizer Event", EventStatus.PENDING.value),
        ("Approved Organizer Event", EventStatus.APPROVED.value),
    ]
    other_events = [("Other User Event", EventStatus.APPROVED.value)]
    other_user = _register_user(client)

    _create_events_for_user(auth_user["user"]["id"], category.id, own_events)
    _create_events_for_user(other_user["user"]["id"], category.id, other_events)

    response = client.get(
        f"/api/users/{auth_user['user']['id']}/events",
        headers=auth_user["headers"],
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "items" in data and "pagination" in data
    titles = [item["title"] for item in data["items"]]
    assert set(titles) == {title for title, _ in own_events}
    assert other_events[0][0] not in titles
    assert data["pagination"]["total"] == len(own_events)
    assert all(item["organizer"]["id"] == auth_user["user"]["id"] for item in data["items"])
    assert {item["status"] for item in data["items"]} == {status for _, status in own_events}


def test_organizer_events_listing_requires_auth(client: TestClient, auth_user: Dict):
    response = client.get(f"/api/users/{auth_user['user']['id']}/events")

    assert response.status_code == 401
    assert "not authenticated" in detail_message(response)


def test_organizer_cannot_view_other_users_events(client: TestClient, auth_user: Dict, category_factory):
    category = category_factory(name="Private Events")
    owner = _register_user(client)
    _create_events_for_user(owner["user"]["id"], category.id, [("Owner Only Event", EventStatus.APPROVED.value)])

    response = client.get(
        f"/api/users/{owner['user']['id']}/events",
        headers=auth_user["headers"],
    )

    assert response.status_code == 403
    assert "not authorized" in detail_message(response)
