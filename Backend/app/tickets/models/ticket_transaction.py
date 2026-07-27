from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
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
    from app.events.models import Event
    from .ticket import Ticket


class TicketTransactionType(str, Enum):
    PURCHASE = "purchase"
    TRANSFER = "transfer"
    REFUND = "refund"
    RESALE = "resale"


class TicketTransaction(Base):
    __tablename__ = "ticket_transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    seller_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="transactions",
        lazy="selectin",
    )
    event: Mapped["Event"] = relationship("Event", lazy="selectin")
    buyer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[buyer_id],
        lazy="selectin",
    )
    seller: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[seller_id],
        lazy="selectin",
    )

