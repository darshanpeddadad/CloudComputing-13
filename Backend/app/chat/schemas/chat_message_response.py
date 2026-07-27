from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .user_summary import ChatUserSummary


class ChatMessageResponse(BaseModel):
    """Serialized chat message for HTTP responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    room_id: str
    sender_id: Optional[str]
    content: str
    sent_at: datetime
    sender: Optional[ChatUserSummary] = None
