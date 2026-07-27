from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class EventCreateDTO(BaseModel):


    title: str
    description: str
    location: str
    latitude: float
    longitude: float
    category_id: str
    organizer_id: str
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    status: Optional[str] = None  # Optional, will be ignored and set to pending
    max_attendees: int = Field(gt=0)
    image_urls: Optional[List[str]] = []

    @model_validator(mode="after")
    def validate_dates_and_times(self):


        # Rule 1: End date cannot be before start date
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")

        # Rule 2: Same-day time check
        if (
            self.start_date == self.end_date
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")

        return self
