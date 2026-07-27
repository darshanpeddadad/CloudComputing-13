from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TicketTypeCreateRequest(BaseModel):
    name: str
    price: float = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=1, max_length=10)
    capacity: int = Field(..., gt=0)
    max_per_user: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    resale_allowed: bool
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None


class TicketTypeUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=1, max_length=10)
    capacity: Optional[int] = Field(default=None, gt=0)
    max_per_user: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    resale_allowed: Optional[bool] = None
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None


class TicketTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    capacity: int
    max_per_user: Optional[int] = None
    resale_allowed: bool
    sale_starts_at: Optional[datetime] = None
    sale_ends_at: Optional[datetime] = None
