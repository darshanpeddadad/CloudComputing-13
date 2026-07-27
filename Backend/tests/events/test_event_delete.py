import asyncio
import pytest
from fastapi.testclient import TestClient
from app.auth.models import User
from app.database import SessionLocal
from app.events.models import Event
from tests.events.utils import count_events, create_event_for_user

def _fresh_count() -> int:
    async def _run():
        async with SessionLocal() as session:
            return await count_events(session)
    return asyncio.run(_run())

def _event_exists(event_id: str) -> bool:
    async def _run():
        async with SessionLocal() as session:
            event = await session.get(Event, event_id)
            return event is not None
    return asyncio.run(_run())

def test_admin_can_delete_any_event(client: TestClient, auth_admin, event_factory):
    event_data = event_factory(title="Delete Me")
    event = event_data["event"]
    response = client.delete(f"/api/events/{event.id}", headers=auth_admin["headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    assert _fresh_count() == 0
    assert _event_exists(event.id) is False

def test_organizer_can_delete_their_event(client: TestClient, auth_user, category_factory):
    category = category_factory(name="Student Life")
    async def _create():
        async with SessionLocal() as session:
            user = await session.get(User, auth_user["user"]["id"])
            event = await create_event_for_user(session, organizer=user, category=category, title="Organizer Event")
            await session.commit()
            return event.id
    event_id = asyncio.run(_create())
    response = client.delete(f"/api/events/{event_id}", headers=auth_user["headers"])
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert _fresh_count() == 0
    assert _event_exists(event_id) is False

def test_non_organizer_cannot_delete_event(client: TestClient, auth_user, event_factory):
    event_data = event_factory(title="Protected Event")
    event = event_data["event"]
    response = client.delete(f"/api/events/{event.id}", headers=auth_user["headers"])
    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert _event_exists(event.id) is True

def test_anonymous_user_cannot_delete_event(client: TestClient, event_factory):
    event_data = event_factory(title="Anon Cannot Delete")
    event = event_data["event"]
    response = client.delete(f"/api/events/{event.id}")
    assert response.status_code == 401
    assert _event_exists(event.id) is True

def test_delete_nonexistent_event_returns_404(client: TestClient, auth_admin):
    response = client.delete("/api/events/non-existent", headers=auth_admin["headers"])
    assert response.status_code == 404
    payload = response.json()
    assert "detail" in payload
