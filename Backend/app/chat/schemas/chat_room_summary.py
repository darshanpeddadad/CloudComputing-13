from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .chat_message_response import ChatMessageResponse
from .participant_summary import ChatParticipantSummary
from .user_summary import ChatUserSummary


class ChatRoomSummary(BaseModel):
    """Room summary with latest message and unread count."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    room_type: str
    event_id: Optional[str] = None
    context: Optional[str] = None
    title: Optional[str] = None
    unread_count: int
    last_message: Optional[ChatMessageResponse] = None
    participants: list[ChatParticipantSummary] = Field(default_factory=list)
    other_user: Optional[ChatUserSummary] = None
