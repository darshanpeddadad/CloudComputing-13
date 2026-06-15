from fastapi.testclient import TestClient

from Backend.tests.auth.utils import auth_url, detail_message, make_email, registration_payload


def test_register_accepts_hs_fulda_subdomains_and_returns_profile(client: TestClient):
    payload = registration_payload(
        email=make_email(domain="informatik.hs-fulda.de"),
        interests=["ai", "robotics", "events"],
    )

    response = client.post(auth_url("/register"), json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == payload["email"]
    assert data["first_names"] == payload["first_names"]
    assert data["last_name"] == payload["last_name"]
    assert data["dob"] == payload["dob"]
    assert data["interests"] == payload["interests"]
    assert data["roles"] == ["user"]
    assert data["id"]


def test_register_allows_root_hs_fulda_domain(client: TestClient):
    payload = registration_payload(email=make_email(domain="hs-fulda.de"))

    response = client.post(auth_url("/register"), json=payload)

    assert response.status_code == 201
    assert response.json()["data"]["roles"] == ["user"]


def test_register_rejects_non_fulda_domain(client: TestClient):
    payload = registration_payload(email="person@gmail.com")

    response = client.post(auth_url("/register"), json=payload)

    assert response.status_code == 422
    assert "hs-fulda.de" in detail_message(response)


def test_register_requires_interests(client: TestClient):
    payload = registration_payload(interests=[])

    response = client.post(auth_url("/register"), json=payload)

    assert response.status_code == 422
    assert "interest" in detail_message(response)


def test_register_requires_matching_passwords(client: TestClient):
    payload = registration_payload(confirm_password="Mismatch123")

    response = client.post(auth_url("/register"), json=payload)

    assert response.status_code == 422
    assert "password" in detail_message(response)
