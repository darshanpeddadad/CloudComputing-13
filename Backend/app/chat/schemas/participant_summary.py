from typing import Optional

from pydantic import BaseModel


class ChatParticipantSummary(BaseModel):
    user_id: str
    role: str
    name: Optional[str] = None
