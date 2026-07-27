from __future__ import annotations

from datetime import date, time
from typing import List

from pydantic import BaseModel

from .event_category_schema import EventCategorySchema
from .event_organizer_schema import EventOrganizerSchema


class EventResponse(BaseModel):
    id: str
    title: str
    description: str
    location: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    sos_enabled: bool
    max_attendees: int
    status: str
    category: EventCategorySchema
    organizer: EventOrganizerSchema
    images: List[str]
