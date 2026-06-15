from fastapi.testclient import TestClient

from Backend.tests.auth.utils import auth_url, decode_token, detail_message, login_payload, registration_payload


def test_login_returns_token_and_user_payload(client: TestClient):
    password = "SecurePass1!"
    email = registration_payload()["email"]
    create_response = client.post(
        auth_url("/register"),
        json=registration_payload(email=email, password=password),
    )
    assert create_response.status_code == 201

    response = client.post(auth_url("/login"), json=login_payload(email=email, password=password))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    data = body["data"]
    assert data["token_type"] == "bearer"
    token_payload = decode_token(data["access_token"])
    assert token_payload["sub"] == data["user"]["id"]
    assert token_payload["email"] == email.lower()
    assert data["user"]["email"] == email
    assert data["user"]["roles"] == ["user"]


def test_login_rejects_invalid_credentials(client: TestClient):
    email = registration_payload()["email"]
    client.post(auth_url("/register"), json=registration_payload(email=email))

    response = client.post(auth_url("/login"), json=login_payload(email=email, password="WrongPass123"))

    assert response.status_code == 401
    assert "invalid" in detail_message(response)
