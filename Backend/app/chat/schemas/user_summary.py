from pydantic import BaseModel


class ChatUserSummary(BaseModel):
    """Lightweight user details for chat payloads."""

    id: str
    name: str
