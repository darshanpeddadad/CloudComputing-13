import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.tickets.models import TicketType
from Backend.tests.events.utils import create_category, make_event_payload


def _create_category(name: str = "Live Events"):
    async def _run():
        async with SessionLocal() as session:
            category = await create_category(session, name)
            await session.commit()
            await session.refresh(category)
            return category

    return asyncio.run(_run())


def _create_event_for_user(client: TestClient, auth_user) -> str:
    category = _create_category()
    payload = make_event_payload(
        category_id=category.id,
        organizer_id=auth_user["user"]["id"],
    )
    import json
    # Event creation now requires multipart/form-data with event_data as JSON string
    data = {"event_data": json.dumps(payload)}
    response = client.post("/api/events/", data=data, headers=auth_user["headers"])
    assert response.status_code == 201, f"Create event failed: {response.text}"
    return response.json()["data"]["id"]


def _count_ticket_types() -> int:
    async def _run():
        async with SessionLocal() as session:
            total = await session.scalar(select(func.count(TicketType.id)))
            return int(total or 0)

    return asyncio.run(_run())


def _get_ticket_type(ticket_type_id: str) -> TicketType | None:
    async def _run():
        async with SessionLocal() as session:
            return await session.get(TicketType, ticket_type_id)

    return asyncio.run(_run())


def test_ticket_type_creation_requires_resale_allowed(client: TestClient, auth_user):
    event_id = _create_event_for_user(client, auth_user)
    payload = {
        "name": "General Admission",
        "price": 25.00,
        "currency": "USD",
        "capacity": 150,
    }

    response = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=payload,
        headers=auth_user["headers"],
    )

    assert response.status_code == 422
    assert "resale_allowed" in str(response.json()).lower()
    assert _count_ticket_types() == 0


def test_ticket_type_creation_accepts_resale_allowed_true_and_false(
    client: TestClient,
    auth_user,
):
    event_id = _create_event_for_user(client, auth_user)

    payload_true = {
        "name": "VIP",
        "price": 99.99,
        "currency": "USD",
        "capacity": 50,
        "max_per_user": 2,
        "resale_allowed": True,
    }
    response_true = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=payload_true,
        headers=auth_user["headers"],
    )
    assert response_true.status_code == 201
    data_true = response_true.json()["data"]
    assert data_true["event_id"] == event_id
    assert data_true["name"] == payload_true["name"]
    assert data_true["resale_allowed"] is True

    created_true = _get_ticket_type(data_true["id"])
    assert created_true is not None
    assert created_true.resale_allowed is True

    payload_false = {
        "name": "Balcony",
        "price": 45.50,
        "currency": "USD",
        "capacity": 200,
        "resale_allowed": False,
    }
    response_false = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=payload_false,
        headers=auth_user["headers"],
    )
    assert response_false.status_code == 201
    data_false = response_false.json()["data"]
    assert data_false["resale_allowed"] is False

    created_false = _get_ticket_type(data_false["id"])
    assert created_false is not None
    assert created_false.resale_allowed is False


def test_ticket_type_list_returns_event_ticket_types(client: TestClient, auth_user):
    event_id = _create_event_for_user(client, auth_user)

    payloads = [
        {"name": "VIP", "price": 100.0, "currency": "USD", "capacity": 30, "resale_allowed": True},
        {"name": "GA", "price": 25.0, "currency": "USD", "capacity": 300, "resale_allowed": False},
    ]
    created_ids = []
    for payload in payloads:
        resp = client.post(
            f"/api/events/{event_id}/ticket-types",
            json=payload,
            headers=auth_user["headers"],
        )
        assert resp.status_code == 201
        created_ids.append(resp.json()["data"]["id"])

    # Listing ticket types should be public (no authentication required)
    list_response = client.get(f"/api/events/{event_id}/ticket-types")
    assert list_response.status_code == 200
    data = list_response.json()["data"]
    assert len(data) == 2
    names = {item["name"] for item in data}
    assert names == {"VIP", "GA"}
    assert {item["id"] for item in data} == set(created_ids)


def test_ticket_type_update_allows_resale_flag_change(client: TestClient, auth_user):
    event_id = _create_event_for_user(client, auth_user)
    create_payload = {
        "name": "Balcony",
        "price": 45.50,
        "currency": "USD",
        "capacity": 200,
        "resale_allowed": False,
    }
    create_resp = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=create_payload,
        headers=auth_user["headers"],
    )
    assert create_resp.status_code == 201
    ticket_type_id = create_resp.json()["data"]["id"]

    update_payload = {
        "price": 55.00,
        "capacity": 180,
        "resale_allowed": True,
        "name": "Balcony Prime",
    }
    update_resp = client.patch(
        f"/api/events/{event_id}/ticket-types/{ticket_type_id}",
        json=update_payload,
        headers=auth_user["headers"],
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["name"] == "Balcony Prime"
    assert updated["price"] == update_payload["price"]
    assert updated["capacity"] == update_payload["capacity"]
    assert updated["resale_allowed"] is True

    db_ticket_type = _get_ticket_type(ticket_type_id)
    assert db_ticket_type is not None
    assert db_ticket_type.name == "Balcony Prime"
    assert float(db_ticket_type.price) == update_payload["price"]
    assert db_ticket_type.capacity == update_payload["capacity"]
    assert db_ticket_type.resale_allowed is True


def test_ticket_type_delete_removes_record(client: TestClient, auth_user):
    event_id = _create_event_for_user(client, auth_user)
    payload = {
        "name": "Student",
        "price": 10.0,
        "currency": "USD",
        "capacity": 100,
        "resale_allowed": False,
    }
    create_resp = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=payload,
        headers=auth_user["headers"],
    )
    assert create_resp.status_code == 201
    ticket_type_id = create_resp.json()["data"]["id"]

    delete_resp = client.delete(
        f"/api/events/{event_id}/ticket-types/{ticket_type_id}",
        headers=auth_user["headers"],
    )
    assert delete_resp.status_code == 200
    assert _get_ticket_type(ticket_type_id) is None
    assert _count_ticket_types() == 0


def test_ticket_type_detail_returns_data(client: TestClient, auth_user):
    event_id = _create_event_for_user(client, auth_user)
    payload = {
        "name": "Front Row",
        "price": 150.0,
        "currency": "USD",
        "capacity": 20,
        "resale_allowed": True,
    }
    create_resp = client.post(
        f"/api/events/{event_id}/ticket-types",
        json=payload,
        headers=auth_user["headers"],
    )
    assert create_resp.status_code == 201
    ticket_type_id = create_resp.json()["data"]["id"]

    detail_resp = client.get(
        f"/api/events/{event_id}/ticket-types/{ticket_type_id}",
        headers=auth_user["headers"],
    )
    assert detail_resp.status_code == 200
    data = detail_resp.json()["data"]
    assert data["id"] == ticket_type_id
    assert data["event_id"] == event_id
    assert data["name"] == payload["name"]
    assert data["capacity"] == payload["capacity"]
    assert data["resale_allowed"] is True
