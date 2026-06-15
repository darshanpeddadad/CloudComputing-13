from datetime import date, time, timedelta
from typing import Callable, Dict

import pytest
from fastapi.testclient import TestClient


def test_events_listing_is_public(client: TestClient, event_factory: Callable[..., Dict]):
    event_factory()

    response = client.get("/api/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "items" in data
    assert "pagination" in data


def test_events_listing_returns_all_required_fields(client: TestClient, event_factory: Callable[..., Dict]):
    custom_image_urls = [
        "https://s3.amazonaws.com/fulda-events/images/tech-fair-main.jpg",
        "https://s3.amazonaws.com/fulda-events/images/tech-fair-side.jpg",
    ]
    event_factory(
        title="Fulda Innovation Summit",
        description="Innovation fair for startups",
        location="Fulda Campus",
        latitude=50.551,
        longitude=9.678,
        start_date=date(2025, 6, 10),
        end_date=date(2025, 6, 12),
        start_time=time(9, 30),
        end_time=time(17, 0),
        category_name="Innovation",
        organizer_first_names="Mila",
        organizer_last_name="Reis",
        sos_enabled=False,
        max_attendees=1200,
        image_urls=custom_image_urls,
    )

    response = client.get("/api/events")

    assert response.status_code == 200
    data = response.json()["data"]["items"]
    assert len(data) == 1
    event = data[0]
    assert event["title"] == "Fulda Innovation Summit"
    assert event["description"] == "Innovation fair for startups"
    assert event["location"] == "Fulda Campus"
    assert event["latitude"] == pytest.approx(50.551)
    assert event["longitude"] == pytest.approx(9.678)
    assert event["start_date"] == "2025-06-10"
    assert event["end_date"] == "2025-06-12"
    assert event["start_time"] == "09:30:00"
    assert event["end_time"] == "17:00:00"
    assert event["sos_enabled"] is False
    assert event["max_attendees"] == 1200
    assert event["category"]["name"] == "Innovation"
    assert event["organizer"]["name"] == "Mila Reis"
    assert event["organizer"]["id"]
    assert event["images"] == custom_image_urls


def test_events_listing_sorted_by_soonest_start(client: TestClient, event_factory: Callable[..., Dict]):
    event_factory(title="Future Robotics Expo", start_date=date(2025, 7, 20), start_time=time(12, 0))
    event_factory(title="AI Meetup", start_date=date(2025, 4, 5), start_time=time(9, 0))
    event_factory(title="Cybersecurity Forum", start_date=date(2025, 4, 5), start_time=time(8, 0))

    response = client.get("/api/events")

    items = response.json()["data"]["items"]
    titles = [item["title"] for item in items]
    assert titles == ["Cybersecurity Forum", "AI Meetup", "Future Robotics Expo"]


def test_events_listing_supports_pagination(client: TestClient, event_factory: Callable[..., Dict]):
    for offset in range(5):
        event_factory(
            title=f"Paginated Event {offset}",
            start_date=date(2025, 5, 1) + timedelta(days=offset),
            start_time=time(10 + offset, 0),
        )

    page_one = client.get("/api/events", params={"page": 1, "page_size": 2})
    assert page_one.status_code == 200
    body = page_one.json()["data"]
    assert len(body["items"]) == 2
    assert body["pagination"] == {"page": 1, "page_size": 2, "total": 5, "pages": 3, "has_next": True}
    assert [item["title"] for item in body["items"]] == ["Paginated Event 0", "Paginated Event 1"]

    page_two = client.get("/api/events", params={"page": 2, "page_size": 2})
    assert page_two.status_code == 200
    second_body = page_two.json()["data"]
    assert len(second_body["items"]) == 2
    assert second_body["pagination"]["page"] == 2
    assert [item["title"] for item in second_body["items"]] == ["Paginated Event 2", "Paginated Event 3"]

    page_three = client.get("/api/events", params={"page": 3, "page_size": 2})
    third_body = page_three.json()["data"]
    assert len(third_body["items"]) == 1
    assert third_body["pagination"]["has_next"] is False


def test_events_listing_can_filter_by_category(client: TestClient, event_factory: Callable[..., Dict]):
    event_factory(title="Tech Expo", category_name="Technology")
    event_factory(title="Art Festival", category_name="Arts")
    event_factory(title="AI Symposium", category_name="Technology")

    tech_response = client.get("/api/events", params={"category": "Technology"})
    assert tech_response.status_code == 200
    tech_titles = [item["title"] for item in tech_response.json()["data"]["items"]]
    assert tech_titles == ["AI Symposium", "Tech Expo"]

    arts_response = client.get("/api/events", params={"category": "Arts"})
    assert arts_response.status_code == 200
    arts_titles = [item["title"] for item in arts_response.json()["data"]["items"]]
    assert arts_titles == ["Art Festival"]


def test_events_listing_supports_search_by_title(client: TestClient, event_factory: Callable[..., Dict]):
    event_factory(title="Fulda Tech Expo", category_name="Technology", start_date=date(2025, 5, 1), start_time=time(9, 0))
    event_factory(title="Fulda Art Gala", category_name="Arts", start_date=date(2025, 5, 2), start_time=time(10, 0))
    event_factory(title="Berlin Tech Meetup", category_name="Technology", start_date=date(2025, 5, 3), start_time=time(11, 0))

    response = client.get("/api/events", params={"search": "tech"})
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["data"]["items"]]
    assert titles == ["Fulda Tech Expo", "Berlin Tech Meetup"]

    second_response = client.get("/api/events", params={"search": "fulda"})
    assert second_response.status_code == 200
    second_titles = [item["title"] for item in second_response.json()["data"]["items"]]
    assert second_titles == ["Fulda Tech Expo", "Fulda Art Gala"]


def test_events_listing_shows_only_approved_events(client: TestClient, event_factory: Callable[..., Dict]):
    event_factory(title="Approved Event", status="approved")
    event_factory(title="Pending Event", status="pending")
    event_factory(title="Rejected Event", status="rejected")

    response = client.get("/api/events")

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    titles = [item["title"] for item in items]
    assert titles == ["Approved Event"]
