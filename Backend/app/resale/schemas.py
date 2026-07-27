from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, condecimal
from app.events.schemas import EventResponse
from app.resale.models.ticket_resale_listing import TicketResaleStatus

class TicketResaleListingBase(BaseModel):
    ticket_id: str = Field(..., description="UUID of the ticket to resell")
    asking_price: float = Field(..., gt=0, description="Price at which the ticket is being sold")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code (e.g. USD)")
    allow_offers: bool = Field(default=True, description="Whether buyers can make offers lower than the asking price")
    auto_accept_price: Optional[float] = Field(None, gt=0, description="If set, offers at or above this price are automatically accepted")
    expires_at: Optional[datetime] = Field(None, description="When the listing expires")
    notes: Optional[str] = Field(None, description="Additional notes from the seller")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
                "asking_price": 50.00,
                "currency": "USD",
                "allow_offers": True,
                "expires_at": "2024-12-31T23:59:59Z",
                "notes": "Great seat!"
            }
        }
    }

class TicketResaleListingCreate(TicketResaleListingBase):
    pass

class TicketResaleListingUpdate(BaseModel):
    asking_price: Optional[float] = Field(None, gt=0)
    allow_offers: Optional[bool] = None
    auto_accept_price: Optional[float] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class TicketResaleListingResponse(TicketResaleListingBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "listing-123",
                "ticket_id": "123e4567-e89b-12d3-a456-426614174000",
                "seller_id": "user-abc",
                "buyer_id": None,
                "status": "active",
                "asking_price": 60.0,
                "currency": "USD",
                "allow_offers": True,
                "auto_accept_price": None,
                "expires_at": None,
                "notes": "Great seat!",
                "created_at": "2024-08-01T12:00:00Z",
                "updated_at": "2024-08-01T12:00:00Z",
                "sale_completed_at": None,
                "event": {
                    "id": "event-456",
                    "title": "Test Resale Event",
                    "description": "Event for resale testing",
                    "location": "Test Venue",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "start_date": "2024-09-01",
                    "end_date": "2024-09-01",
                    "start_time": "18:00:00",
                    "end_time": "20:00:00",
                    "sos_enabled": False,
                    "max_attendees": 100,
                    "status": "approved",
                    "category": {"id": "cat-1", "name": "Music"},
                    "organizer": {"id": "user-abc", "name": "Alice Smith"},
                    "images": [],
                },
            }
        },
    )

    id: str
    seller_id: str
    buyer_id: Optional[str] = None
    status: TicketResaleStatus
    created_at: datetime
    updated_at: datetime
    sale_completed_at: Optional[datetime] = None
    event: Optional[EventResponse] = None

class TicketResaleOfferBase(BaseModel):
    offered_price: float = Field(..., gt=0)
    message: Optional[str] = None

class TicketResaleOfferCreate(TicketResaleOfferBase):
    pass

class TicketResaleOfferResponse(TicketResaleOfferBase):
    id: str
    listing_id: str
    buyer_id: str
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
