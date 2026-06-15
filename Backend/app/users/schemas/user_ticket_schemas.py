from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool


class UserTicketSummary(BaseModel):
    ticket_id: str
    ticket_type_id: str | None = None
    ticket_type: str | None = None
    ticket_type_description: str | None = None
    ticket_type_price: float | None = None
    ticket_type_currency: str | None = None
    resale_allowed: bool | None = None
    seat_label: str | None = None
    qr_code: str | None = None
    metadata: dict | None = None
    price: float | None = None
    status: str
    purchased_at: datetime | None = None
    checked_in_at: datetime | None = None
    cancelled_at: datetime | None = None
    event_id: str
    event_name: str
    event_description: str | None = None
    event_location: str | None = None
    event_date: str | None = None
    event_time: str | None = None
    event_end_date: str | None = None
    event_end_time: str | None = None
    event_image: str | None = None


class UserTicketDetail(BaseModel):
    ticket_id: str
    ticket_type_id: str | None = None
    ticket_type: str | None = None
    ticket_type_description: str | None = None
    ticket_type_price: float | None = None
    ticket_type_currency: str | None = None
    resale_allowed: bool | None = None
    seat_label: str | None = None
    qr_code: str | None = None
    metadata: dict | None = None
    price: float | None = None
    status: str
    purchased_at: datetime | None = None
    checked_in_at: datetime | None = None
    cancelled_at: datetime | None = None
    event_id: str
    event_name: str
    event_description: str | None
    event_location: str | None = None
    event_date: str | None
    event_time: str | None
    event_end_date: str | None = None
    event_end_time: str | None = None
    event_image: str | None = None


class UserTicketsListData(BaseModel):
    items: list[UserTicketSummary]
    pagination: Pagination


class UserTicketListResponse(BaseModel):
    success: bool
    data: UserTicketsListData


class UserTicketDetailResponse(BaseModel):
    success: bool
    data: UserTicketDetail