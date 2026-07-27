import asyncio
import os
import sys
from pathlib import Path
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = TESTS_DIR.parent

if BACKEND_ROOT.name.lower() == "backend":
    REPO_ROOT = BACKEND_ROOT.parent
else:
    REPO_ROOT = BACKEND_ROOT

for path in (REPO_ROOT, BACKEND_ROOT):
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)

if BACKEND_ROOT.name.lower() == "backend":
    from main import app  # noqa: E402
else:  # Running from inside Backend/ (e.g., Docker volume)
    from main import app  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.auth.models import Role, User  # noqa: E402
from tests.auth.utils import auth_url, registration_payload  # noqa: E402

def _resolve_sqlite_path() -> Path:
    """Derive the SQLite file path from DATABASE_URL (defaults handled)."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url and ":///" in db_url:
        raw_path = db_url.split(":///")[-1]
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            return (REPO_ROOT / candidate).resolve()
        return candidate
    return (BACKEND_ROOT / "test.db").resolve()

@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Ensure the SQLite test database exists with the latest schema."""
    db_path = _resolve_sqlite_path()
    if db_path.exists():
        db_path.unlink()
    legacy_path = (BACKEND_ROOT / "test.db").resolve()
    if legacy_path != db_path and legacy_path.exists():
        legacy_path.unlink()
    asyncio.run(init_db())

@pytest.fixture()
def client() -> TestClient:
    """FastAPI test client fixture scoped per test."""
    return TestClient(app)

@pytest.fixture()
def auth_user(client: TestClient) -> Dict:
    """Register and log in a user, returning id and auth headers."""
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
        "user": {**data["user"], "password": password},
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

def _grant_role(user_id: str, role_name: str = "admin") -> None:
    async def _run():
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            assert user is not None, "User not found when granting role"
            result = await session.execute(select(Role).where(Role.name == role_name))
            role = result.scalars().first()
            if not role:
                role = Role(id=f"role-{role_name}", name=role_name)
                session.add(role)
                await session.flush([role])
            if role not in user.roles:
                user.roles.append(role)
            await session.commit()

    asyncio.run(_run())

@pytest.fixture()
def auth_admin(client: TestClient, auth_user) -> Dict:
    """Register and log in a user with the admin role."""
    base = auth_user  # Use injected fixture value
    _grant_role(base["user"]["id"], "admin")
    return base
