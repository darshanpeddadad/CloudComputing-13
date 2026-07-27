from pydantic import BaseModel


class EventOrganizerSchema(BaseModel):
    id: str
    name: str
