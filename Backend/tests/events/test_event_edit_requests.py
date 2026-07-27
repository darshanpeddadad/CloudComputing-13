import json

from fastapi.testclient import TestClient

from Backend.tests.auth.utils import auth_url, registration_payload
from Backend.tests.events.utils import make_event_payload


def _register_and_login(client: TestClient) -> dict:
    payload = registration_payload()
    password = payload["password"]
    register_response = client.post(auth_url("/register"), json=payload)
    assert register_response.status_code == 201

    login_response = client.post(
        auth_url("/login"),
        json={"email": payload["email"], "password": password},
    )
    assert login_response.status_code == 200
    data = login_response.json()["data"]
    token = data["access_token"]
    return {
        "user": data["user"],
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def _create_event(client: TestClient, organizer: dict, category_id: str, **overrides) -> dict:
    payload = make_event_payload(
        category_id=category_id,
        organizer_id=organizer["user"]["id"],
        **overrides,
    )
    data = {"event_data": json.dumps(payload)}
    response = client.post("/api/events", data=data, headers=organizer["headers"])
    assert response.status_code == 201
    return response.json()["data"]


def test_event_edit_request_approval_updates_event(
    client: TestClient,
    auth_admin: dict,
    category_factory,
):
    organizer = _register_and_login(client)
    category = category_factory(name="Technology")

    event = _create_event(
        client,
        organizer,
        category.id,
        title="Original Title",
        location="Old Location",
        max_attendees=100,
    )

    edit_payload = {
        "title": "Updated Title",
        "location": "New Location",
        "max_attendees": 150,
    }
    edit_response = client.post(
        f"/api/events/{event['id']}/edit-requests",
        json=edit_payload,
        headers=organizer["headers"],
    )
    assert edit_response.status_code == 200
    edit_request = edit_response.json()["data"]
    assert edit_request["status"] == "pending"
    assert edit_request["changes"]["title"]["from"] == "Original Title"
    assert edit_request["changes"]["title"]["to"] == "Updated Title"
    assert edit_request["requested_by"]["id"] == organizer["user"]["id"]

    pending_response = client.get(
        "/api/events/edit-requests",
        params={"status": "pending"},
        headers=auth_admin["headers"],
    )
    assert pending_response.status_code == 200
    pending_items = pending_response.json()["data"]["items"]
    assert len(pending_items) == 1
    assert pending_items[0]["id"] == edit_request["id"]

    approve_response = client.post(
        f"/api/events/edit-requests/{edit_request['id']}/approve",
        json={"review_note": "Looks good"},
        headers=auth_admin["headers"],
    )
    assert approve_response.status_code == 200
    approved = approve_response.json()["data"]
    assert approved["status"] == "approved"
    assert approved["review_note"] == "Looks good"
    assert approved["reviewer"]["id"] == auth_admin["user"]["id"]
    assert approved["reviewed_at"] is not None
    assert approved["event"]["title"] == "Updated Title"
    assert approved["event"]["location"] == "New Location"
    assert approved["event"]["max_attendees"] == 150

    event_response = client.get(f"/api/events/{event['id']}")
    assert event_response.status_code == 200
    updated_event = event_response.json()["data"]
    assert updated_event["title"] == "Updated Title"
    assert updated_event["location"] == "New Location"
    assert updated_event["max_attendees"] == 150


def test_event_edit_request_reject_does_not_update_event(
    client: TestClient,
    auth_admin: dict,
    category_factory,
):
    organizer = _register_and_login(client)
    category = category_factory(name="Arts")

    event = _create_event(
        client,
        organizer,
        category.id,
        title="Original Title",
        location="Old Location",
    )

    edit_response = client.post(
        f"/api/events/{event['id']}/edit-requests",
        json={"title": "Rejected Title"},
        headers=organizer["headers"],
    )
    assert edit_response.status_code == 200
    edit_request = edit_response.json()["data"]

    reject_response = client.post(
        f"/api/events/edit-requests/{edit_request['id']}/reject",
        json={"review_note": "Not acceptable"},
        headers=auth_admin["headers"],
    )
    assert reject_response.status_code == 200
    rejected = reject_response.json()["data"]
    assert rejected["status"] == "rejected"
    assert rejected["review_note"] == "Not acceptable"
    assert rejected["reviewer"]["id"] == auth_admin["user"]["id"]
    assert rejected["reviewed_at"] is not None
    assert rejected["event"]["title"] == "Original Title"

    event_response = client.get(f"/api/events/{event['id']}")
    assert event_response.status_code == 200
    unchanged_event = event_response.json()["data"]
    assert unchanged_event["title"] == "Original Title"
    assert unchanged_event["location"] == "Old Location"


def test_event_edit_request_approve_requires_admin(
    client: TestClient,
    auth_user: dict,
    category_factory,
):
    category = category_factory(name="Science")
    event = _create_event(
        client,
        auth_user,
        category.id,
        title="Original Title",
    )

    edit_response = client.post(
        f"/api/events/{event['id']}/edit-requests",
        json={"title": "Attempted Update"},
        headers=auth_user["headers"],
    )
    assert edit_response.status_code == 200
    edit_request = edit_response.json()["data"]

    approve_response = client.post(
        f"/api/events/edit-requests/{edit_request['id']}/approve",
        headers=auth_user["headers"],
    )
    assert approve_response.status_code == 403


def test_event_edit_request_reject_requires_admin(
    client: TestClient,
    auth_user: dict,
    category_factory,
):
    category = category_factory(name="History")
    event = _create_event(
        client,
        auth_user,
        category.id,
        title="Original Title",
    )

    edit_response = client.post(
        f"/api/events/{event['id']}/edit-requests",
        json={"title": "Attempted Update"},
        headers=auth_user["headers"],
    )
    assert edit_response.status_code == 200
    edit_request = edit_response.json()["data"]

    reject_response = client.post(
        f"/api/events/edit-requests/{edit_request['id']}/reject",
        headers=auth_user["headers"],
    )
    assert reject_response.status_code == 403


def test_event_edit_requests_mine_only_returns_requesting_user(
    client: TestClient,
    category_factory,
):
    category = category_factory(name="Sports")
    organizer_a = _register_and_login(client)
    organizer_b = _register_and_login(client)

    event_a = _create_event(client, organizer_a, category.id, title="Org A Event")
    event_b = _create_event(client, organizer_b, category.id, title="Org B Event")

    edit_a = client.post(
        f"/api/events/{event_a['id']}/edit-requests",
        json={"title": "Org A Updated"},
        headers=organizer_a["headers"],
    )
    assert edit_a.status_code == 200

    edit_b = client.post(
        f"/api/events/{event_b['id']}/edit-requests",
        json={"title": "Org B Updated"},
        headers=organizer_b["headers"],
    )
    assert edit_b.status_code == 200

    list_response = client.get(
        "/api/events/edit-requests/mine",
        headers=organizer_a["headers"],
    )
    assert list_response.status_code == 200
    items = list_response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["event"]["title"] == "Org A Event"
