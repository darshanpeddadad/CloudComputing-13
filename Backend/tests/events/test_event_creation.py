import asyncio
from datetime import date

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.events.models import Event, EventStatus
from Backend.tests.events.utils import count_events, make_event_payload


def _count_events_in_db() -> int:
    async def _run():
        async with SessionLocal() as session:
            return await count_events(session)

    return asyncio.run(_run())


def _get_event(event_id: str):
    async def _run():
        async with SessionLocal() as session:
            return await session.get(Event, event_id)

    return asyncio.run(_run())


import json

def test_authenticated_user_can_create_event(client: TestClient, auth_user, category_factory):
    category = category_factory(name="Technology")
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
    )

    # Convert payload to form-data compatible format
    data = {
        "event_data": json.dumps(payload)
    }

    response = client.post(
        "/api/events", 
        data=data,  # Use 'data' for form fields
        headers=auth_user["headers"]
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    data = body["data"]
    assert data["id"]
    assert data["title"] == payload["title"]
    assert data["status"] == EventStatus.PENDING.value
    assert data["category"]["id"] == category.id
    assert data["category"]["name"] == category.name
    assert data["organizer"]["id"] == auth_user["user"]["id"]

    db_event = _get_event(data["id"])
    assert db_event is not None
    assert str(db_event.status) == EventStatus.PENDING.value
    assert db_event.organizer_id == auth_user["user"]["id"]
    assert db_event.category_id == category.id


def test_anonymous_user_cannot_create_event(client: TestClient, category_factory):
    category = category_factory(name="Arts & Culture")
    payload = make_event_payload(category_id=category.id, organizer_id="anonymous-user")

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}
    )

    assert response.status_code == 401
    assert "message" in response.json()
    assert _count_events_in_db() == 0


def test_event_start_time_must_be_before_end_time_on_same_day(client: TestClient, auth_user, category_factory):
    category = category_factory(name="Sports")
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
        start_date=date(2025, 7, 1).isoformat(),
        end_date=date(2025, 7, 1).isoformat(),
        start_time="18:00:00",
        end_time="16:30:00",
    )

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}, 
        headers=auth_user["headers"]
    )

    assert response.status_code == 422
    detail_text = str(response.json())
    assert "after start_time" in detail_text.lower()
    assert _count_events_in_db() == 0


def test_event_end_date_cannot_be_before_start_date(client: TestClient, auth_user, category_factory):
    category = category_factory(name="Business")
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
        start_date=date(2025, 9, 10).isoformat(),
        end_date=date(2025, 9, 9).isoformat(),
    )

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}, 
        headers=auth_user["headers"]
    )

    assert response.status_code == 422
    assert "end_date" in str(response.json()).lower()
    assert _count_events_in_db() == 0


def test_created_events_default_to_pending_status_even_if_payload_attempts_override(
    client: TestClient,
    auth_user,
    category_factory,
):
    category = category_factory(name="Innovation")
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
        status="approved",
    )

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}, 
        headers=auth_user["headers"]
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == EventStatus.PENDING.value

    db_event = _get_event(data["id"])
    assert str(db_event.status) == EventStatus.PENDING.value


def test_category_must_exist_before_event_creation(client: TestClient, auth_user):
    payload = make_event_payload(
        category_id="missing-category-id",
        organizer_id=auth_user["user"]["id"],
    )

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}, 
        headers=auth_user["headers"]
    )

    assert response.status_code == 404
    assert _count_events_in_db() == 0


def test_max_attendees_must_be_positive_integer(client: TestClient, auth_user, category_factory):
    category = category_factory(name="Wellness")
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
        max_attendees=0,
    )

    response = client.post(
        "/api/events", 
        data={"event_data": json.dumps(payload)}, 
        headers=auth_user["headers"]
    )

    assert response.status_code == 422
    assert "max_attendees" in str(response.json()).lower()
    assert _count_events_in_db() == 0
