from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from app.chat.models import ChatParticipantRole


def _role_priority(role: str) -> int:
    return 2 if role == ChatParticipantRole.OWNER.value else 1


@dataclass
class EventGroupRoom:
    event_id: str
    room_id: str
    database_room_id: Optional[str] = None
    user_roles: Dict[str, str] = field(default_factory=dict)
    user_sids: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    sid_user: Dict[str, str] = field(default_factory=dict)

    def add_member(self, user_id: str, sid: str, role: str) -> None:
        self.sid_user[sid] = user_id
        self.user_sids[user_id].add(sid)

        existing_role = self.user_roles.get(user_id)
        if existing_role == ChatParticipantRole.OWNER.value:
            return
        if _role_priority(role) > _role_priority(existing_role or role):
            self.user_roles[user_id] = role
        else:
            self.user_roles[user_id] = existing_role or role

    def remove_sid(self, sid: str) -> Tuple[Optional[str], bool]:
        user_id = self.sid_user.pop(sid, None)
        if not user_id:
            return None, False

        sids = self.user_sids.get(user_id, set())
        sids.discard(sid)
        removed_user = False
        if not sids:
            self.user_sids.pop(user_id, None)
            self.user_roles.pop(user_id, None)
            removed_user = True
        return user_id, removed_user

    def remove_user(self, user_id: str) -> List[str]:
        sids = list(self.user_sids.pop(user_id, set()))
        for sid in sids:
            self.sid_user.pop(sid, None)
        self.user_roles.pop(user_id, None)
        return sids

    def participants_payload(self) -> List[dict]:
        items = [
            {"user_id": user_id, "role": role}
            for user_id, role in self.user_roles.items()
        ]
        return sorted(items, key=lambda item: (item["role"] != ChatParticipantRole.OWNER.value, item["user_id"]))

    def is_empty(self) -> bool:
        return not self.user_roles

    def sids(self) -> List[str]:
        all_sids: List[str] = []
        for sids in self.user_sids.values():
            all_sids.extend(list(sids))
        return all_sids


class EventGroupRoomState:
    """Tracks membership and roles for event group chat rooms."""

    def __init__(self) -> None:
        self._rooms: Dict[str, EventGroupRoom] = {}
        self._sid_room: Dict[str, str] = {}

    def _get_or_create_room(self, room_id: str, event_id: str) -> EventGroupRoom:
        if room_id not in self._rooms:
            self._rooms[room_id] = EventGroupRoom(event_id=event_id, room_id=room_id)
        return self._rooms[room_id]

    def track_join(self, sid: str, room_id: str, event_id: str, user_id: str, role: str, database_room_id: Optional[str] = None) -> None:
        room = self._get_or_create_room(room_id, event_id)
        room.add_member(user_id, sid, role)
        if database_room_id:
            room.database_room_id = database_room_id
        self._sid_room[sid] = room_id
    
    def database_room_id_for_room(self, room_id: str) -> Optional[str]:
        room = self._rooms.get(room_id)
        return room.database_room_id if room else None

    def is_member(self, sid: str, room_id: str) -> bool:
        return self._sid_room.get(sid) == room_id

    def participants_payload(self, room_id: str) -> List[dict]:
        room = self._rooms.get(room_id)
        if not room:
            return []
        return room.participants_payload()

    def remove_sid(self, sid: str) -> Optional[Tuple[str, str, bool]]:
        room_id = self._sid_room.pop(sid, None)
        if not room_id:
            return None

        room = self._rooms.get(room_id)
        if not room:
            return None

        _, removed_user = room.remove_sid(sid)
        if room.is_empty():
            self._rooms.pop(room_id, None)
        return room_id, room.event_id, removed_user

    def remove_user(self, room_id: str, user_id: str) -> List[str]:
        room = self._rooms.get(room_id)
        if not room:
            return []
        sids = room.remove_user(user_id)
        for sid in sids:
            self._sid_room.pop(sid, None)
        if room.is_empty():
            self._rooms.pop(room_id, None)
        return sids

    def event_id_for_room(self, room_id: str) -> Optional[str]:
        room = self._rooms.get(room_id)
        return room.event_id if room else None

    def sids_for_room(self, room_id: str) -> List[str]:
        room = self._rooms.get(room_id)
        if not room:
            return []
        return room.sids()

    def clear(self) -> None:
        self._rooms.clear()
        self._sid_room.clear()
