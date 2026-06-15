import uuid
from datetime import date
from typing import Any, Dict, List

from app.auth.security.jwt_service import decode_access_token
from jose import JWTError


def make_email(local_part: str = "user", domain: str = "hs-fulda.de") -> str:
    """Generate a unique hs-fulda email for isolation between tests."""
    return f"{local_part}-{uuid.uuid4().hex[:6]}@{domain}"


def registration_payload(**overrides: Any) -> Dict[str, Any]:
    """Base payload for registration requests with sensible defaults."""
    password = overrides.get("password", "SecurePass1!")
    payload: Dict[str, Any] = {
        "first_names": "Alex Maximilian",
        "last_name": "Fulda",
        "email": make_email(domain="informatik.hs-fulda.de"),
        "dob": str(overrides.get("dob", date(2000, 1, 1))),
        "password": password,
        "confirm_password": overrides.get("confirm_password", password),
        "interests": ["ai", "robotics"],
    }
    payload.update(overrides)
    return payload


def login_payload(email: str, password: str) -> Dict[str, str]:
    return {"email": email, "password": password}


def detail_message(response) -> str:
    payload = response.json()
    if "error" in payload:
        error = payload["error"]
        details = error.get("details")
        if isinstance(details, list):
            messages: List[str] = []
            for entry in details:
                if isinstance(entry, dict):
                    messages.append(entry.get("msg", ""))
                else:
                    messages.append(str(entry))
            detail_text = " ".join(messages)
        elif isinstance(details, dict):
            detail_text = " ".join(str(v) for v in details.values())
        else:
            detail_text = str(details or "")
        combined = f"{error.get('message', '')} {detail_text}".strip()
        return combined.lower()

    detail = payload.get("detail")
    if isinstance(detail, list):
        messages = [str(err) for err in detail]
        return " ".join(messages).lower()
    return str(detail or "").lower()


def auth_url(path: str) -> str:
    """Build full API path for auth routes."""
    return f"/api/auth{path}"


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT access token, raising if invalid."""
    try:
        return decode_access_token(token)
    except JWTError as exc:
        raise AssertionError(f"Token failed to decode: {exc}") from exc
