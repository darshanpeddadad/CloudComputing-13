import asyncio
import pytest
from fastapi.testclient import TestClient
from app.database import SessionLocal
from tests.events.utils import create_event_with_dependencies

@pytest.fixture
def event_data():
    async def _create():
        async with SessionLocal() as session:
            data = await create_event_with_dependencies(session)
            await session.commit()
            return data
    return asyncio.run(_create())

def test_create_bookmark(client: TestClient, auth_user, event_data):
    user_id = auth_user["user"]["id"]
    event_id = event_data["event"].id
    headers = auth_user["headers"]

    response = client.post(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 201
    assert response.json()["message"] == "Bookmark added successfully"
    response = client.post(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 409

def test_check_bookmark_status(client: TestClient, auth_user, event_data):
    user_id = auth_user["user"]["id"]
    event_id = event_data["event"].id
    headers = auth_user["headers"]

    # Initially false
    response = client.get(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_bookmarked"] is False

    # Create bookmark
    client.post(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)

    # Now true
    response = client.get(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_bookmarked"] is True

def test_get_user_bookmarks(client: TestClient, auth_user, event_data):
    user_id = auth_user["user"]["id"]
    event_id = event_data["event"].id
    headers = auth_user["headers"]

    # Create bookmark
    client.post(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)

    response = client.get(f"/api/users/{user_id}/bookmarks", headers=headers)
    assert response.status_code == 200
    bookmarks = response.json()
    assert len(bookmarks) >= 1
    assert bookmarks[0]["event_id"] == event_id
    assert bookmarks[0]["event"]["id"] == event_id

def test_delete_bookmark(client: TestClient, auth_user, event_data):
    user_id = auth_user["user"]["id"]
    event_id = event_data["event"].id
    headers = auth_user["headers"]

    # Create bookmark
    client.post(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)

    # Delete bookmark
    response = client.delete(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.json()["is_bookmarked"] is False

    # Delete non-existent bookmark
    response = client.delete(f"/api/users/{user_id}/bookmarks/{event_id}", headers=headers)
    assert response.status_code == 404
