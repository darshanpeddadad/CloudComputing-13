from pydantic import BaseModel


class UnreadRoomEntry(BaseModel):
    room_id: str
    unread: int


class UnreadSummary(BaseModel):
    total: int
    rooms: list[UnreadRoomEntry]
