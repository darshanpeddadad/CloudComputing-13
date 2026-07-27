from pydantic import BaseModel
from typing import List
from app.events.schemas.event_response import EventResponse

class BookmarkStatus(BaseModel):
    is_bookmarked: bool

class BookmarkResponse(BaseModel):
    user_id: str
    event_id: str
    event: EventResponse

    class Config:
        from_attributes = True
