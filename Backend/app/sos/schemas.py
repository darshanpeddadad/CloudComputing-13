from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.sos.models import SOSStatus


class SOSAlertBase(BaseModel):
    pass


class SOSAlertCreate(SOSAlertBase):
    event_id: str
    latitude: float = Field(..., description="Latitude of the user triggering SOS")
    longitude: float = Field(..., description="Longitude of the user triggering SOS")
    message: Optional[str] = Field(None, description="Optional SOS message")


class SOSAlertUpdate(SOSAlertBase):
    status: SOSStatus
    resolver_id: Optional[str] = None


class SOSUserDetails(BaseModel):
    id: str
    first_names: str
    last_name: str
    email: EmailStr
    dob: str
    roles: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)

    @field_validator("roles", mode="before")
    @classmethod
    def _extract_role_names(cls, value):
        if not value:
            return []
        return [role.name if hasattr(role, "name") else str(role) for role in value]

    @field_validator("interests", mode="before")
    @classmethod
    def _extract_interest_names(cls, value):
        if not value:
            return []
        return [interest.name if hasattr(interest, "name") else str(interest) for interest in value]

    class Config:
        from_attributes = True


class SOSEventDetails(BaseModel):
    id: str
    title: str
    location: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    sos_enabled: bool
    status: str
    max_attendees: int
    organizer_id: str

    class Config:
        from_attributes = True


class SOSAlertResponse(SOSAlertBase):
    id: str
    event_id: str
    user_id: str
    status: SOSStatus
    latitude: float
    longitude: float
    message: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    resolver_id: Optional[str]
    user: SOSUserDetails
    event: SOSEventDetails
    resolver: Optional[SOSUserDetails] = None

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class SOSAlertListResponse(BaseModel):
    items: list[SOSAlertResponse]
    pagination: Pagination
