from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from .event_edit_request_status import EventEditRequestStatus

if TYPE_CHECKING:
    from app.auth.models.user import User
    from .event import Event


class EventEditRequest(Base):
    __tablename__ = "event_edit_requests"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'approved', 'rejected')",
            name="ck_event_edit_requests_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requested_by_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventEditRequestStatus.PENDING.value,
    )

    changes: Mapped[Dict[str, Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    event: Mapped["Event"] = relationship("Event", back_populates="edit_requests", lazy="selectin")
    requested_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[requested_by_id],
        lazy="selectin",
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewer_id],
        lazy="selectin",
    )
