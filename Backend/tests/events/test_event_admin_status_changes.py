import asyncio
from typing import Callable, Dict

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.events.models import Event, EventStatus


def _get_event_status(event_id: str) -> str:
    async def _run():
        async with SessionLocal() as session:
            event = await session.get(Event, event_id)
            return event.status if event else None

    return asyncio.run(_run())


def test_admin_can_approve_pending_event(
    client: TestClient, auth_admin: Dict, event_factory: Callable[..., Dict]
):
    pending_event = event_factory(title="Approve Me", status=EventStatus.PENDING.value)["event"]

    response = client.post(f"/api/events/{pending_event.id}/approve", headers=auth_admin["headers"])

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Event approved successfully"
    data = body["data"]
    assert data["id"] == pending_event.id
    assert data["status"] == EventStatus.APPROVED.value
    assert data["category"]["id"]
    assert data["organizer"]["id"]
    assert _get_event_status(pending_event.id) == EventStatus.APPROVED.value


def test_non_admin_cannot_approve_event(
    client: TestClient, auth_user: Dict, event_factory: Callable[..., Dict]
):
    pending_event = event_factory(status=EventStatus.PENDING.value)["event"]

    response = client.post(f"/api/events/{pending_event.id}/approve", headers=auth_user["headers"])

    assert response.status_code == 403
    assert "admin role required" in str(response.json()["detail"]).lower()
    assert _get_event_status(pending_event.id) == EventStatus.PENDING.value


def test_cannot_approve_non_pending_event(
    client: TestClient, auth_admin: Dict, event_factory: Callable[..., Dict]
):
    approved_event = event_factory(title="Already Approved", status=EventStatus.APPROVED.value)["event"]

    response = client.post(f"/api/events/{approved_event.id}/approve", headers=auth_admin["headers"])

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Only pending events can be approved."
    assert _get_event_status(approved_event.id) == EventStatus.APPROVED.value


def test_approve_missing_event_returns_404(client: TestClient, auth_admin: Dict):
    response = client.post("/api/events/missing-id/approve", headers=auth_admin["headers"])

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "Event not found."


def test_admin_can_reject_pending_event(
    client: TestClient, auth_admin: Dict, event_factory: Callable[..., Dict]
):
    pending_event = event_factory(title="Reject Me", status=EventStatus.PENDING.value)["event"]

    response = client.post(f"/api/events/{pending_event.id}/reject", headers=auth_admin["headers"])

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Event rejected successfully"
    data = payload["data"]
    assert data["id"] == pending_event.id
    assert data["status"] == EventStatus.REJECTED.value
    assert _get_event_status(pending_event.id) == EventStatus.REJECTED.value


def test_non_admin_cannot_reject_event(
    client: TestClient, auth_user: Dict, event_factory: Callable[..., Dict]
):
    pending_event = event_factory(status=EventStatus.PENDING.value)["event"]

    response = client.post(f"/api/events/{pending_event.id}/reject", headers=auth_user["headers"])

    assert response.status_code == 403
    assert "admin role required" in str(response.json()["detail"]).lower()
    assert _get_event_status(pending_event.id) == EventStatus.PENDING.value


def test_cannot_reject_non_pending_event(
    client: TestClient, auth_admin: Dict, event_factory: Callable[..., Dict]
):
    approved_event = event_factory(title="Not Pending", status=EventStatus.APPROVED.value)["event"]

    response = client.post(f"/api/events/{approved_event.id}/reject", headers=auth_admin["headers"])

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Only pending events can be rejected."
    assert _get_event_status(approved_event.id) == EventStatus.APPROVED.value


def test_reject_missing_event_returns_404(client: TestClient, auth_admin: Dict):
    response = client.post("/api/events/missing-id/reject", headers=auth_admin["headers"])

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "Event not found."
