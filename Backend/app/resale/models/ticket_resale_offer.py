from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .ticket_resale_listing import TicketResaleListing


class TicketResaleOfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class TicketResaleOffer(Base):
    __tablename__ = "ticket_resale_offers"
    __table_args__ = (
        CheckConstraint(
            f"status in ('{TicketResaleOfferStatus.PENDING.value}', "
            f"'{TicketResaleOfferStatus.ACCEPTED.value}', '{TicketResaleOfferStatus.DECLINED.value}', "
            f"'{TicketResaleOfferStatus.WITHDRAWN.value}', '{TicketResaleOfferStatus.EXPIRED.value}')",
            name="ck_resale_offers_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    listing_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ticket_resale_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    offered_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketResaleOfferStatus.PENDING.value,
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    listing: Mapped["TicketResaleListing"] = relationship(
        "TicketResaleListing",
        back_populates="offers",
        lazy="selectin",
    )
    buyer: Mapped["User"] = relationship("User", lazy="selectin")

