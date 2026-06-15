from pydantic import BaseModel


class CategoryResponse(BaseModel):
    """Response schema for event category."""
    id: str
    name: str
