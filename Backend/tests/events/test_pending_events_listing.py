import asyncio
from datetime import date, time
from typing import Callable, Dict, List

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.events.models import Event, EventStatus


def _get_event_status(event_id: str) -> str:
    async def _run():
        async with SessionLocal() as session:
            event = await session.get(Event, event_id)
            return event.status if event else None

    return asyncio.run(_run())


def _extract_titles(items: List[Dict]) -> List[str]:
    return [item["title"] for item in items]


def test_admin_can_list_pending_events_with_pagination(
    client: TestClient, auth_admin: Dict, event_factory: Callable[..., Dict]
):
    pending_titles = [f"Pending Event {idx}" for idx in range(1, 4)]
    for idx, title in enumerate(pending_titles):
        event_factory(
            title=title,
            status=EventStatus.PENDING.value,
            start_date=date(2025, 5, idx + 1),
            start_time=time(9 + idx, 0),
        )
    event_factory(title="Approved Event", status=EventStatus.APPROVED.value)

    first_page = client.get(
        "/api/events/pending",
        params={"page": 1, "page_size": 2},
        headers=auth_admin["headers"],
    )
    assert first_page.status_code == 200
    payload = first_page.json()
    assert payload["success"] is True
    assert payload["message"] == "Pending events fetched successfully"
    data = payload["data"]
    assert data["pagination"] == {"page": 1, "page_size": 2, "total": 3, "pages": 2, "has_next": True}
    assert _extract_titles(data["items"]) == pending_titles[:2]
    assert {item["status"] for item in data["items"]} == {EventStatus.PENDING.value}

    second_page = client.get(
        "/api/events/pending",
        params={"page": 2, "page_size": 2},
        headers=auth_admin["headers"],
    )
    assert second_page.status_code == 200
    second_data = second_page.json()["data"]
    assert second_data["pagination"]["page"] == 2
    assert second_data["pagination"]["has_next"] is False
    assert _extract_titles(second_data["items"]) == pending_titles[2:]


def test_pending_events_listing_requires_admin(client: TestClient, auth_user: Dict):
    response = client.get("/api/events/pending", headers=auth_user["headers"])

    assert response.status_code == 403
    assert "admin role required" in str(response.json()["detail"]).lower()


def test_anonymous_user_cannot_list_pending_events(client: TestClient):
    response = client.get("/api/events/pending")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated."
