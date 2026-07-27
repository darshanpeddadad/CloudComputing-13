from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.events.models import Event
    from app.tickets.models import Ticket


class ParticipationStatus(str, Enum):
    REGISTERED = "registered"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class EventParticipation(Base):
    __tablename__ = "event_participations"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "user_id",
            name="uq_event_participations_event_user",
        ),
        CheckConstraint(
            f"status in ('{ParticipationStatus.REGISTERED.value}', "
            f"'{ParticipationStatus.ATTENDED.value}', '{ParticipationStatus.NO_SHOW.value}')",
            name="ck_event_participations_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ParticipationStatus.REGISTERED.value,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="participations",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")
    ticket: Mapped[Optional["Ticket"]] = relationship("Ticket", lazy="selectin")

