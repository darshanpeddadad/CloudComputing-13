from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class TicketPurchaseItem(BaseModel):
    ticket_type_id: str
    quantity: int = Field(default=1, ge=1)


class TicketPurchaseRequest(BaseModel):
    event_id: str
    # Backward compatibility
    ticket_type_id: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    # Cart mode
    items: List[TicketPurchaseItem] = Field(default_factory=list)
    # Reward redemption fields
    redeem_points: Optional[int] = None  # Points to redeem for discount


class TicketPurchaseResponse(BaseModel):
    ticket_id: str
    ticket_ids: List[str] = []
    event_id: str
    status: str
    message: str
    # Reward information
    points_awarded: int = 0
    new_point_balance: int = 0
    badge_upgraded: bool = False
    new_badge_name: Optional[str] = None
    # Redemption information
    points_redeemed: int = 0
    discount_applied: float = 0.0
    final_price: float = 0.0

