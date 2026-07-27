from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserListQuery(BaseModel):
    """Query parameters for listing users with pagination."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=50, description="Number of items per page (max 50)")
    search: Optional[str] = Field(None, description="Search term for filtering users by name or email")

    @field_validator("search")
    @classmethod
    def _normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
