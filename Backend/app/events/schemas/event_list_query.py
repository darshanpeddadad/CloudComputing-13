from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EventListQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=50)
    category: Optional[str] = None
    search: Optional[str] = None
    location: Optional[str] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    min_attendees: Optional[int] = Field(default=None, ge=1)
    max_attendees: Optional[int] = Field(default=None, ge=1)
    time_filter: Optional[str] = None
    semantic_event_ids: Optional[list[str]] = None
    use_semantic_search: bool = False
    sort_by: str = "start_date_asc"

    @field_validator("category", "search", "location")
    @classmethod
    def _normalize_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("time_filter")
    @classmethod
    def _validate_time_filter(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        allowed = {"upcoming", "ongoing", "past"}
        if normalized not in allowed:
            raise ValueError("time_filter must be one of: upcoming, ongoing, past")
        return normalized

    @field_validator("sort_by")
    @classmethod
    def _validate_sort_by(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {
            "start_date_asc",
            "start_date_desc",
            "title_asc",
            "title_desc",
            "max_attendees_desc",
            "max_attendees_asc",
        }
        if normalized not in allowed:
            raise ValueError(
                "sort_by must be one of: start_date_asc, start_date_desc, title_asc, "
                "title_desc, max_attendees_desc, max_attendees_asc"
            )
        return normalized

    @field_validator("max_attendees")
    @classmethod
    def _validate_attendee_range(cls, value: Optional[int], info) -> Optional[int]:
        if value is None:
            return None
        min_attendees = info.data.get("min_attendees")
        if min_attendees is not None and value < min_attendees:
            raise ValueError("max_attendees cannot be less than min_attendees")
        return value

    @field_validator("start_date_to")
    @classmethod
    def _validate_date_range(cls, value: Optional[date], info) -> Optional[date]:
        if value is None:
            return None
        start_date_from = info.data.get("start_date_from")
        if start_date_from and value < start_date_from:
            raise ValueError("start_date_to cannot be before start_date_from")
        return value
