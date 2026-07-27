import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Iterable, Optional
from urllib.parse import parse_qs

import socketio
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.admin.routers import get_admin_router
from app.auth.routers import get_auth_router
from app.auth.security.auth_security import AuthSecurity
from app.auth.utils.auth_checks import user_from_token, is_admin
from app.categories.routers import get_category_router
from app.chat import get_chat_http_router, get_chat_router
from app.database import SessionLocal, init_db
from app.events.routers import get_event_router
from app.tickets.routers.ticket_router import get_ticket_router
from app.resale.routers.resale_router import get_resale_router
from app.sos.router import get_sos_router
from app.seeders.auth_seed import seed_roles_and_admin
from app.seeders.event_user_seed import seed_event_users
from app.seeders.event_seed import seed_event_users_and_events
from app.rewards.seeders import seed_reward_levels, seed_reward_data
from app.chats_v2.presentation.direct_events import register_direct_events, direct_room_state
from app.chats_v2.presentation.event_group_events import handle_group_disconnect, register_event_group_events
from app.users.routers.user_ticket_router import get_user_ticket_router
from app.users.routers.user_event_router import get_user_event_router
from app.users.routers.user_details_router import get_user_details_router
from app.rewards.routers import get_reward_router
from app.users.routers.bookmark_router import get_bookmark_router

api_router = APIRouter(prefix="/api")
DEFAULT_DEV_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


@api_router.get("/")
async def root():
    return {"message": "Welcome to Fulda Fall 2025 Team2 API"}


@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth_security = AuthSecurity()
    await init_db()
    async with SessionLocal() as session:
        await seed_roles_and_admin(session, auth_security)
        await seed_reward_levels(session)
        
        # Seed event users and events
        from sqlalchemy import select
        from app.auth.models import Role
        user_role = await session.scalar(select(Role).where(Role.name == "user"))
        if user_role:
            organizers = await seed_event_users(session, auth_security, user_role)
            result, status = await seed_event_users_and_events(session, organizers)
            if status == "seeded":
                logging.info(f"Seeded {result[2]} events with {result[0]} organizers and {result[1]} categories")
            elif status == "events_exist":
                logging.info("Events already exist, skipping event seeding")
            elif status == "no_organizers":
                logging.warning("No organizers available for event seeding")
            
            # Seed reward data for users (profiles, point history, participations)
            await seed_reward_data(session)
    app.state.auth_security = auth_security
    yield


def _parse_cors_origins() -> list[str]:
    """
    Parse BACKEND_CORS_ORIGINS env var.
    Supports either JSON array (recommended) or comma-separated string.
    Falls back to local dev origins when unset.
    """
    raw = os.getenv("BACKEND_CORS_ORIGINS")
    if not raw:
        return DEFAULT_DEV_CORS_ORIGINS.copy()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        if isinstance(parsed, str):
            parsed = [parsed.strip()] if parsed.strip() else []
        elif isinstance(parsed, list):
            parsed = [str(item).strip() for item in parsed if str(item).strip()]
        else:
            parsed = [str(parsed).strip()] if str(parsed).strip() else []

    if not parsed:
        raise RuntimeError(
            "BACKEND_CORS_ORIGINS is set but empty after parsing. "
            "Provide at least one allowed origin."
        )

    return parsed


def _should_allow_credentials(origins: list[str]) -> bool:
    """
    Browsers reject Access-Control-Allow-Origin: * with credentials.
    Disable credentials automatically when wildcard is used.
    """
    return "*" not in origins


app = FastAPI(
    title="Fulda Fall 2025 Team2 API",
    description="Backend API for Fulda Fall 2025 Team2 project",
    version="1.0.0",
    lifespan=lifespan,
)


# ADDED GLOBAL EXCEPTION HANDLER


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Handle custom 401 format for POST /api/events
    # Check if detail is already a dict (custom format from dependency)
    if exc.status_code == 401 and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=401,
            content=exc.detail,
        )
    # All other HTTPExceptions use default FastAPI format with "detail"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# CORS middleware
cors_origins = _parse_cors_origins()

if not cors_origins:
    raise RuntimeError(
        "BACKEND_CORS_ORIGINS resolved to an empty list. "
        "Set at least one allowed origin."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=_should_allow_credentials(cors_origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Socket.IO (ASGI) server
socket_server = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,
    ping_timeout=20,
    ping_interval=25,
)


def _authorization_from_headers(headers: Optional[Iterable[tuple[bytes, bytes]]]) -> Optional[str]:
    for key, value in headers or []:
        if key.decode().lower() == "authorization":
            return value.decode()
    return None


async def _resolve_socket_user(
    auth: Any,
    headers: Optional[Iterable[tuple[bytes, bytes]]],
    query_token: Optional[str] = None,
):
    token: Optional[str] = None
    if isinstance(auth, dict):
        token = auth.get("token") or auth.get("authorization") or auth.get("Authorization")

    if not token and query_token:
        token = query_token

    if token and isinstance(token, str) and not token.lower().startswith("bearer "):
        token = f"Bearer {token}"

    if not token:
        token = _authorization_from_headers(headers)

    if not token:
        return None

    async with SessionLocal() as session:
        user = await user_from_token(session, token)
        if user:
            # Ensure roles are loaded before session closes/detaches
            # This prevents DetachedInstanceError when is_admin check runs later
            await session.refresh(user, attribute_names=["roles"])
        return user


async def _get_socket_session(sid: str) -> dict:
    try:
        return await socket_server.get_session(sid)
    except KeyError:
        return {}


@socket_server.event
async def connect(sid, environ, auth):
    scope = environ.get("asgi.scope") if isinstance(environ, dict) else {}
    headers = scope.get("headers") or []
    query_params = parse_qs(scope.get("query_string", b"").decode()) if scope else {}
    query_token = query_params.get("token", [None])[0]
    user = await _resolve_socket_user(auth, headers, query_token)
    if not user:
        return False  # Reject the connection

    await socket_server.save_session(
        sid,
        {
            "user_id": user.id,
            "email": user.email,
        },
    )

    # Join global admin room if admin
    try:
        if is_admin(user):
            await socket_server.enter_room(sid, "admin_global")
    except Exception as e:
        logger = logging.getLogger("uvicorn.error")
        logger.warning(f"Failed to join admin room for user {user.id}: {e}")
        # Proceed anyway to see if connection succeeds otherwise

    await socket_server.emit(
        "server:connected",
        {"message": "Socket.IO connection established", "user_id": user.id},
        to=sid,
    )


@socket_server.event
async def disconnect(sid):
    direct_room_state.remove_sid(sid)
    await handle_group_disconnect(socket_server, sid)
    session = await _get_socket_session(sid)
    await socket_server.emit(
        "server:disconnected",
        {"user_id": session.get("user_id"), "sid": sid},
    )


@socket_server.on("join_room")
async def join_room(sid, data):
    room = ""
    if isinstance(data, dict):
        room = str(data.get("room") or "").strip()

    if not room:
        await socket_server.emit("server:error", {"message": "room is required"}, to=sid)
        return

    await socket_server.enter_room(sid, room)
    await socket_server.emit("server:room_joined", {"room": room}, to=sid)


@socket_server.on("chat:send")
async def handle_chat_send(sid, data):
    if not isinstance(data, dict):
        await socket_server.emit("server:error", {"message": "Invalid payload"}, to=sid)
        return

    room = str(data.get("room") or "").strip()
    message = str(data.get("message") or data.get("content") or "").strip()
    session = await _get_socket_session(sid)
    sender_id = session.get("user_id")

    if not room or not message:
        await socket_server.emit(
            "server:error",
            {"message": "room and message are required"},
            to=sid,
        )
        return

    payload = {
        "room": room,
        "message": message,
        "sender_id": sender_id,
    }
    await socket_server.emit("chat:message", payload, room=room)


socket_app = socketio.ASGIApp(socket_server, other_asgi_app=app)
register_direct_events(socket_server)
register_event_group_events(socket_server)


app.include_router(api_router)
app.include_router(get_auth_router())
app.include_router(get_admin_router())
app.include_router(get_event_router())
app.include_router(get_category_router())
app.include_router(get_chat_http_router())
app.include_router(get_chat_router())
app.include_router(get_ticket_router())
app.include_router(get_resale_router())
app.include_router(get_sos_router(socket_server))
app.include_router(get_user_ticket_router())
app.include_router(get_user_event_router())
app.include_router(get_user_details_router())
app.include_router(get_reward_router())
app.include_router(get_bookmark_router())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000)
