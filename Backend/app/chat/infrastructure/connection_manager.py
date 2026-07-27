from __future__ import annotations

from typing import Dict, Set

from fastapi import WebSocket


class ChatConnectionManager:
    """Tracks active websocket connections by chat room."""

    def __init__(self) -> None:
        self._rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        # Only accept if not already accepted
        # If already accepted, this will raise RuntimeError which we can safely ignore
        try:
            await websocket.accept()
        except RuntimeError:
            # WebSocket already accepted, which is fine
            pass
        self._rooms.setdefault(room_id, set()).add(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        connections = self._rooms.get(room_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._rooms.pop(room_id, None)

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    async def broadcast(self, room_id: str, message: dict) -> None:
        connections = self._rooms.get(room_id, set())
        for connection in list(connections):
            try:
                await connection.send_json(message)
            except RuntimeError:
                pass


chat_manager = ChatConnectionManager()

