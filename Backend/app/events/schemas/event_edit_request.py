from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from .event_organizer_schema import EventOrganizerSchema
from .event_response import EventResponse


class EventEditRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_attendees: Optional[int] = Field(default=None, gt=0)
    sos_enabled: Optional[bool] = None


class EventEditRequestReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: Optional[str] = None


class EventEditRequestResponse(BaseModel):
    id: str
    event_id: str
    status: str
    changes: Dict[str, Dict[str, Any]]
    requested_by: EventOrganizerSchema
    reviewer: Optional[EventOrganizerSchema] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    event: EventResponse
