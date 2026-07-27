from datetime import date, time
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient


def test_event_details_are_public(client: TestClient, event_factory: Callable[..., Dict]):
    event_data = event_factory(
        title="Public Robotics Day",
        description="Hands-on robotics sessions",
        location="Fulda Makerspace",
        latitude=50.556,
        longitude=9.68,
        start_date=date(2025, 8, 20),
        end_date=date(2025, 8, 21),
        start_time=time(9, 0),
        end_time=time(18, 30),
        category_name="Robotics",
        organizer_first_names="Taylor",
        organizer_last_name="Kim",
        sos_enabled=True,
        max_attendees=400,
        image_urls=[
            "https://s3.amazonaws.com/fulda-events/images/robotics-main.jpg",
            "https://s3.amazonaws.com/fulda-events/images/robotics-secondary.jpg",
        ],
    )
    event = event_data["event"]

    response = client.get(f"/api/events/{event.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Success"
    data = payload["data"]
    assert data["id"] == event.id
    assert data["title"] == "Public Robotics Day"
    assert data["description"] == "Hands-on robotics sessions"
    assert data["location"] == "Fulda Makerspace"
    assert data["latitude"] == pytest.approx(50.556)
    assert data["longitude"] == pytest.approx(9.68)
    assert data["start_date"] == "2025-08-20"
    assert data["end_date"] == "2025-08-21"
    assert data["start_time"] == "09:00:00"
    assert data["end_time"] == "18:30:00"
    assert data["sos_enabled"] is True
    assert data["max_attendees"] == 400
    assert data["category"]["name"] == "Robotics"
    assert data["organizer"]["name"] == "Taylor Kim"
    assert data["images"] == [
        "https://s3.amazonaws.com/fulda-events/images/robotics-main.jpg",
        "https://s3.amazonaws.com/fulda-events/images/robotics-secondary.jpg",
    ]


def test_event_details_not_found_returns_error_response(client: TestClient):
    response = client.get("/api/events/non-existent-id")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["message"] == "Event not found"
    assert "data" not in payload
