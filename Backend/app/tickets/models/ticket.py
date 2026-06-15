from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.events.models import Event
    from .ticket_type import TicketType
    from .ticket_transaction import TicketTransaction
    from .ticket_assignment import TicketAssignment
    from app.resale.models import TicketResaleListing


class TicketStatus(str, Enum):
    ISSUED = "issued"
    LISTED = "listed"
    CHECKED_IN = "checked_in"
    TRANSFERRED = "transferred"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            f"status in ('{TicketStatus.ISSUED.value}', '{TicketStatus.LISTED.value}', "
            f"'{TicketStatus.CHECKED_IN.value}', "
            f"'{TicketStatus.TRANSFERRED.value}', '{TicketStatus.REFUNDED.value}', '{TicketStatus.CANCELLED.value}')",
            name="ck_tickets_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_type_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TicketStatus.ISSUED.value,
    )
    seat_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    qr_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    purchased_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    ticket_type: Mapped["TicketType"] = relationship(
        "TicketType",
        back_populates="tickets",
        lazy="selectin",
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="tickets",
        lazy="selectin",
    )
    owner: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )
    transactions: Mapped[List["TicketTransaction"]] = relationship(
        "TicketTransaction",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    assignment: Mapped[Optional["TicketAssignment"]] = relationship(
        "TicketAssignment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    resale_listings: Mapped[List["TicketResaleListing"]] = relationship(
        "TicketResaleListing",
        back_populates="ticket",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
