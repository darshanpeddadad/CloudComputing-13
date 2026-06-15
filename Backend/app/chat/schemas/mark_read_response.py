from typing import Optional

from pydantic import BaseModel


class MarkReadResponse(BaseModel):
    room_id: str
    unread: int
    last_read_message_id: Optional[str] = None
