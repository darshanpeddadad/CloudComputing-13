from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.events.models import Event
    from app.tickets.models import Ticket
    from .user_reward_profile import UserRewardProfile


class UserRewardLedger(Base):
    __tablename__ = "user_reward_ledger"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("user_reward_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    points_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    profile: Mapped["UserRewardProfile"] = relationship(
        "UserRewardProfile",
        back_populates="ledger_entries",
        lazy="selectin",
    )
    event: Mapped[Optional["Event"]] = relationship("Event", lazy="selectin")
    ticket: Mapped[Optional["Ticket"]] = relationship("Ticket", lazy="selectin")

