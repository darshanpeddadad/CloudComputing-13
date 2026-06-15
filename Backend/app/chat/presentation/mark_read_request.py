from pydantic import BaseModel


class MarkReadRequest(BaseModel):
    message_id: str
