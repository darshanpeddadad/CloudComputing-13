from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .ticket import Ticket


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"
    __table_args__ = (
        UniqueConstraint("ticket_id", name="uq_ticket_assignments_ticket"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_user_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    guest_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guest_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    ticket: Mapped["Ticket"] = relationship(
        "Ticket",
        back_populates="assignment",
        lazy="selectin",
    )
    assigned_user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
    )

