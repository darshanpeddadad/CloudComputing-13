import uuid

from fastapi.testclient import TestClient

from tests.auth.utils import auth_url, detail_message, registration_payload


def _register_user(client: TestClient):
    """Register and log in a fresh user, returning auth headers and user data."""
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


def _purchase_ticket(client: TestClient, headers: dict, event_setup):
    """Purchase a single ticket for the provided event setup."""
    payload = {
        "event_id": event_setup["event"].id,
        "ticket_type_id": event_setup["ticket_type"].id,
    }
    response = client.post("/api/tickets/purchase", json=payload, headers=headers)
    assert response.status_code == 200
    return response.json()["data"]["ticket_id"]


def test_auth_required_for_user_ticket_endpoints(client: TestClient, auth_user):
    user_id = auth_user["user"]["id"]

    list_response = client.get(f"/api/users/{user_id}/tickets")
    assert list_response.status_code == 401
    assert "not authenticated" in detail_message(list_response)

    detail_response = client.get(f"/api/users/{user_id}/tickets/{uuid.uuid4()}")
    assert detail_response.status_code == 401
    assert "not authenticated" in detail_message(detail_response)


def test_user_ticket_list_has_pagination(client: TestClient, auth_user, approved_event_with_ticket_type):
    event_setup = approved_event_with_ticket_type()
    for _ in range(3):
        _purchase_ticket(client, auth_user["headers"], event_setup)

    first_page = client.get(
        f"/api/users/{auth_user['user']['id']}/tickets",
        params={"page": 1, "page_size": 2},
        headers=auth_user["headers"],
    )
    assert first_page.status_code == 200
    payload = first_page.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "items" in data and "pagination" in data
    assert data["pagination"] == {"page": 1, "page_size": 2, "total": 3, "pages": 2, "has_next": True}
    assert len(data["items"]) == 2

    second_page = client.get(
        f"/api/users/{auth_user['user']['id']}/tickets",
        params={"page": 2, "page_size": 2},
        headers=auth_user["headers"],
    )
    assert second_page.status_code == 200
    second_data = second_page.json()["data"]
    assert second_data["pagination"]["page"] == 2
    assert second_data["pagination"]["has_next"] is False
    assert len(second_data["items"]) == 1


def test_cannot_view_other_users_tickets(client: TestClient, auth_user, approved_event_with_ticket_type):
    event_setup = approved_event_with_ticket_type()
    ticket_id = _purchase_ticket(client, auth_user["headers"], event_setup)
    other_user = _register_user(client)

    list_response = client.get(
        f"/api/users/{auth_user['user']['id']}/tickets",
        headers=other_user["headers"],
    )
    assert list_response.status_code == 403
    assert "not authorized" in detail_message(list_response)

    detail_response = client.get(
        f"/api/users/{auth_user['user']['id']}/tickets/{ticket_id}",
        headers=other_user["headers"],
    )
    assert detail_response.status_code == 403
    assert "not authorized" in detail_message(detail_response)


def test_random_user_id_rejected(client: TestClient, auth_user):
    random_user_id = str(uuid.uuid4())
    response = client.get(f"/api/users/{random_user_id}/tickets", headers=auth_user["headers"])
    assert response.status_code == 403
    assert "not authorized" in detail_message(response)


def test_missing_ticket_returns_404(client: TestClient, auth_user):
    missing_ticket_id = str(uuid.uuid4())

    response = client.get(
        f"/api/users/{auth_user['user']['id']}/tickets/{missing_ticket_id}",
        headers=auth_user["headers"],
    )

    assert response.status_code == 404
    assert "ticket not found" in detail_message(response)
