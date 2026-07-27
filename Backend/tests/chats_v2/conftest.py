import asyncio
import socket
import threading
import time

import pytest
import pytest_asyncio
import uvicorn

import main
from app.chats_v2.presentation.direct_events import direct_room_state
from app.chats_v2.presentation.event_group_events import event_group_state
from Backend.tests.chats_v2.utils import DirectSocketClient, EventGroupSocketClient


def _allocate_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest_asyncio.fixture()
async def socketio_url():
    """Start the Socket.IO ASGI app on an ephemeral port."""
    # Clear state before starting new server instance
    direct_room_state.clear()
    event_group_state.clear()
    
    port = _allocate_port()
    config = uvicorn.Config(
        main.socket_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        lifespan="on",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        deadline = time.time() + 10
        while not server.started:
            if time.time() > deadline:
                raise RuntimeError("Socket.IO test server failed to start")
            await asyncio.sleep(0.05)

        yield f"http://127.0.0.1:{port}"
    finally:
        # Clear state after server shutdown to prevent leakage to next test
        direct_room_state.clear()
        event_group_state.clear()
        # Force server shutdown
        server.should_exit = True
        # Give it a moment to start shutting down
        await asyncio.sleep(0.1)
        # Wait for thread to finish, but don't block forever
        thread.join(timeout=2)
        if thread.is_alive():
            # Thread didn't finish, but it's daemon so it will be killed when process exits
            pass


@pytest.fixture(autouse=True)
def reset_room_state():
    """Reset chat room state before and after each test to ensure test isolation."""
    direct_room_state.clear()
    event_group_state.clear()
    yield
    direct_room_state.clear()
    event_group_state.clear()


@pytest.fixture()
def direct_socket_client_factory():
    """Factory for creating Socket.IO direct chat clients."""

    def _factory(base_url: str, token: str) -> DirectSocketClient:
        return DirectSocketClient(base_url, token)

    return _factory


@pytest.fixture()
def event_group_socket_client_factory():
    """Factory for creating Socket.IO event group chat clients."""

    def _factory(base_url: str, token: str) -> EventGroupSocketClient:
        return EventGroupSocketClient(base_url, token)

    return _factory
