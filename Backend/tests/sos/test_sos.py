import asyncio
from datetime import date, time, timedelta
import json
import pytest
from httpx import AsyncClient

from app.database import SessionLocal
from app.sos.models import SOSStatus
from tests.events.utils import create_category


def create_test_event(client, headers, user_id):
    event_data = {
        "title": "SOS Test Event",
        "description": "Testing SOS functionality",
        "location": "Test Location",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "start_time": "10:00:00",
        "end_time": "18:00:00",
        "max_attendees": 100,
        "sos_enabled": True,
        "organizer_id": user_id,
    }
    
    
    # helper for Category
    # Since we don't have a public create endpoint, we must seed it directly in DB.
    # We use a small async wrapper to use the async session.
    async def _seed_cat():
        async with SessionLocal() as session:
            cat = await create_category(session, "SOS Test Category")
            await session.commit()
            return cat.id

    cat_id = asyncio.run(_seed_cat())
    event_data["category_id"] = cat_id

    # Request using multipart/form-data simulation with `data` map in TestClient
    response = client.post("/api/events/", data={"event_data": json.dumps(event_data)}, headers=headers)
    assert response.status_code == 201, f"Create event failed: {response.text}"
    return response.json()["data"]["id"]


def test_trigger_sos(client, auth_user):
    headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    
    # 1. Create Event
    event_id = create_test_event(client, headers, user_id)
    
    # 2. Trigger SOS
    sos_payload = {
        "event_id": event_id,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "message": "Help me!",
    }
    response = client.post("/api/sos/", json=sos_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == SOSStatus.ACTIVE.value
    assert data["message"] == "Help me!"
    assert data["event_id"] == event_id


def test_list_sos_as_admin(client, auth_admin, auth_user):
    # User creates event and SOS
    user_headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    event_id = create_test_event(client, user_headers, user_id)
    
    sos_payload = {
        "event_id": event_id,
        "latitude": 40.7128,
        "longitude": -74.0060,
    }
    client.post("/api/sos/", json=sos_payload, headers=user_headers)
    
    # Admin lists SOS with pagination
    admin_headers = auth_admin["headers"]
    response = client.get(f"/api/sos/event/{event_id}?page=1&page_size=5", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload and "pagination" in payload
    alerts = payload["items"]
    pagination = payload["pagination"]
    assert len(alerts) >= 1
    assert pagination["page"] == 1
    assert pagination["page_size"] == 5
    assert pagination["total"] >= 1
    assert all(alert["event_id"] == event_id for alert in alerts)
    assert all(alert["status"] == SOSStatus.ACTIVE.value for alert in alerts)


def test_admin_sees_all_sos_for_event(client, auth_admin, auth_user):
    """Admin should see every SOS raised for a given event."""
    user_headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    event_id = create_test_event(client, user_headers, user_id)

    sos_payloads = [
        {"event_id": event_id, "latitude": 10.0, "longitude": 20.0, "message": "First alert"},
        {"event_id": event_id, "latitude": 11.0, "longitude": 21.0, "message": "Second alert"},
    ]
    for payload in sos_payloads:
        res = client.post("/api/sos/", json=payload, headers=user_headers)
        assert res.status_code == 201, f"SOS creation failed: {res.text}"

    admin_headers = auth_admin["headers"]
    response = client.get(f"/api/sos/event/{event_id}", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    alerts = payload["items"]
    pagination = payload["pagination"]
    assert pagination["total"] == len(sos_payloads)
    assert len(alerts) == len(sos_payloads)
    assert all(alert["event_id"] == event_id for alert in alerts)
    assert all(alert["status"] == SOSStatus.ACTIVE.value for alert in alerts)
    # Ensure latest alert is first
    assert alerts[0]["message"] == "Second alert"
    assert alerts[1]["message"] == "First alert"


def test_admin_sos_pagination_and_sorting_latest_first(client, auth_admin, auth_user):
    user_headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    event_id = create_test_event(client, user_headers, user_id)

    messages = ["First alert", "Second alert", "Third alert"]
    for msg in messages:
        res = client.post(
            "/api/sos/",
            json={"event_id": event_id, "latitude": 1.0, "longitude": 1.0, "message": msg},
            headers=user_headers,
        )
        assert res.status_code == 201, f"SOS creation failed: {res.text}"

    admin_headers = auth_admin["headers"]
    resp_page1 = client.get(f"/api/sos/event/{event_id}?page=1&page_size=2", headers=admin_headers)
    assert resp_page1.status_code == 200
    payload1 = resp_page1.json()
    alerts_page1 = payload1["items"]
    pagination1 = payload1["pagination"]

    assert pagination1["page"] == 1
    assert pagination1["page_size"] == 2
    assert pagination1["total"] == len(messages)
    assert pagination1["total_pages"] == 2
    assert [a["message"] for a in alerts_page1] == ["Third alert", "Second alert"]

    resp_page2 = client.get(f"/api/sos/event/{event_id}?page=2&page_size=2", headers=admin_headers)
    assert resp_page2.status_code == 200
    alerts_page2 = resp_page2.json()["items"]
    assert len(alerts_page2) == 1
    assert alerts_page2[0]["message"] == "First alert"


def test_resolve_sos(client, auth_admin, auth_user):
    user_headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    event_id = create_test_event(client, user_headers, user_id)
    
    # Trigger SOS
    sos_payload = {"event_id": event_id, "latitude": 1.0, "longitude": 1.0}
    create_res = client.post("/api/sos/", json=sos_payload, headers=user_headers)
    alert_id = create_res.json()["id"]
    
    # Resolve as Admin
    admin_headers = auth_admin["headers"]
    update_payload = {"status": SOSStatus.RESOLVED.value}
    resolve_res = client.patch(f"/api/sos/{alert_id}", json=update_payload, headers=admin_headers)
    
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == SOSStatus.RESOLVED.value
    assert resolve_res.json()["resolver_id"] == auth_admin["user"]["id"]


def test_admin_lists_all_sos_with_pagination_and_latest_order(client, auth_admin, auth_user):
    user_headers = auth_user["headers"]
    user_id = auth_user["user"]["id"]
    event_id = create_test_event(client, user_headers, user_id)

    messages = ["First alert", "Second alert", "Third alert"]
    for msg in messages:
        res = client.post(
            "/api/sos/",
            json={"event_id": event_id, "latitude": 1.0, "longitude": 1.0, "message": msg},
            headers=user_headers,
        )
        assert res.status_code == 201, f"SOS creation failed: {res.text}"

    admin_headers = auth_admin["headers"]
    page_size = 2
    resp_page1 = client.get(f"/api/sos/?page=1&page_size={page_size}", headers=admin_headers)
    assert resp_page1.status_code == 200
    payload1 = resp_page1.json()
    pagination1 = payload1["pagination"]

    assert pagination1["page"] == 1
    assert pagination1["page_size"] == page_size
    assert pagination1["total"] >= len(messages)
    assert pagination1["total_pages"] >= 1

    # Collect all alerts across pages, maintaining API order (latest first)
    all_alerts = payload1["items"]
    total_pages = pagination1["total_pages"]
    for p in range(2, total_pages + 1):
        resp = client.get(f"/api/sos/?page={p}&page_size={page_size}", headers=admin_headers)
        assert resp.status_code == 200
        all_alerts.extend(resp.json()["items"])

    # Filter to the current event to avoid interference from other tests
    event_alerts = [a for a in all_alerts if a["event_id"] == event_id]
    assert len(event_alerts) >= len(messages)
    # Ensure our event alerts are ordered latest first
    assert [a["message"] for a in event_alerts[:3]] == ["Third alert", "Second alert", "First alert"]


def test_non_admin_cannot_list_all_sos(client, auth_user):
    response = client.get("/api/sos/?page=1&page_size=5", headers=auth_user["headers"])
    assert response.status_code == 403
