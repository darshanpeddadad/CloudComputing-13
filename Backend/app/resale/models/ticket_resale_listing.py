from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
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
    from app.tickets.models import Ticket
    from .ticket_resale_offer import TicketResaleOffer


class TicketResaleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TicketResaleListing(Base):
    __tablename__ = "ticket_resale_listings"
    __table_args__ = (
        CheckConstraint(
            f"status in ('{TicketResaleStatus.DRAFT.value}', '{TicketResaleStatus.ACTIVE.value}', "
            f"'{TicketResaleStatus.RESERVED.value}', '{TicketResaleStatus.SOLD.value}', "
            f"'{TicketResaleStatus.CANCELLED.value}', '{TicketResaleStatus.EXPIRED.value}')",
            name="ck_resale_listings_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketResaleStatus.DRAFT.value,
    )
    asking_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    allow_offers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_accept_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    buyer_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sale_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="resale_listings",
        lazy="selectin",
    )
    seller: Mapped["User"] = relationship(
        "User",
        foreign_keys=[seller_id],
        lazy="selectin",
    )
    buyer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[buyer_id],
        lazy="selectin",
    )
    offers: Mapped[List["TicketResaleOffer"]] = relationship(
        "TicketResaleOffer",
        back_populates="listing",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

