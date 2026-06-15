from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from .user_reward_profile import UserRewardProfile
    from app.offers.models import EventOffer


class RewardLevel(Base):
    __tablename__ = "reward_levels"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    badge_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    profiles: Mapped[List["UserRewardProfile"]] = relationship(
        "UserRewardProfile",
        back_populates="level",
        lazy="selectin",
    )
    offers: Mapped[List["EventOffer"]] = relationship(
        "EventOffer",
        back_populates="required_level",
        lazy="selectin",
    )

