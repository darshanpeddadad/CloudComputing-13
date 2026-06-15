from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .reward_level import RewardLevel
    from .user_reward_ledger import UserRewardLedger


class UserRewardProfile(Base):
    __tablename__ = "user_reward_profiles"

    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    level_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("reward_levels.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lifetime_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_events_joined: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Streak tracking fields
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_week: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "2026-W04" format
    streak_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    
    level_assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    level: Mapped[Optional["RewardLevel"]] = relationship(
        "RewardLevel",
        back_populates="profiles",
        lazy="selectin",
    )
    ledger_entries: Mapped[List["UserRewardLedger"]] = relationship(
        "UserRewardLedger",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

