from datetime import date, time
from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator


class EventCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1, max_length=255)
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    category_id: str
    organizer_id: str
    sos_enabled: bool = False
    max_attendees: int = Field(..., gt=0)
    image_urls: List[str] = Field(default_factory=list)

    @field_validator("image_urls")
    @classmethod
    def _filter_empty_urls(cls, value: List[str]) -> List[str]:
        return [url for url in value if url]

    @model_validator(mode="after")
    def _validate_schedule(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.start_date == self.end_date and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time when start_date equals end_date")
        return self
