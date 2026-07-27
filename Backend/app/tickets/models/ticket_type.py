from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.events.models import Event
    from .ticket import Ticket


class TicketType(Base):
    __tablename__ = "ticket_types"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "name",
            name="uq_ticket_types_event_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resale_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sale_starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sale_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="ticket_types",
        lazy="selectin",
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="ticket_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

