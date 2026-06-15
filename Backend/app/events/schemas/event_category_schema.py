from pydantic import BaseModel


class EventCategorySchema(BaseModel):
    id: str
    name: str
