from collections import defaultdict
from typing import Dict, Optional, Set


class DirectRoomState:
    """Tracks direct chat room context and sid memberships."""

    def __init__(self) -> None:
        self._room_context: Dict[str, str] = {}
        self._room_chat_id: Dict[str, str] = {}
        self._sid_rooms: Dict[str, Set[str]] = defaultdict(set)

    def track_join(self, sid: str, room_id: str, context: str, *, chat_room_id: Optional[str] = None) -> None:
        self._room_context[room_id] = context
        if chat_room_id:
            self._room_chat_id[room_id] = chat_room_id
        self._sid_rooms[sid].add(room_id)

    def is_member(self, sid: str, room_id: str) -> bool:
        return room_id in self._sid_rooms.get(sid, set())

    def context_for_room(self, room_id: str) -> Optional[str]:
        return self._room_context.get(room_id)

    def chat_room_id_for_room(self, room_id: str) -> Optional[str]:
        return self._room_chat_id.get(room_id)

    def remove_sid(self, sid: str) -> None:
        rooms = self._sid_rooms.pop(sid, set())
        # Keep room context; other sids might still be joined.
        for _ in rooms:
            pass

    def clear(self) -> None:
        """Clear all state. Useful for test isolation."""
        self._room_context.clear()
        self._room_chat_id.clear()
        self._sid_rooms.clear()
