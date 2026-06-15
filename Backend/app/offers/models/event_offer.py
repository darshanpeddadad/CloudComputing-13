from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.events.models import Event
    from app.rewards.models import RewardLevel
    from .event_offer_claim import EventOfferClaim


class EventOfferStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class EventOffer(Base):
    __tablename__ = "event_offers"
    __table_args__ = (
        CheckConstraint(
            f"status in ('{EventOfferStatus.DRAFT.value}', '{EventOfferStatus.ACTIVE.value}', "
            f"'{EventOfferStatus.EXPIRED.value}', '{EventOfferStatus.ARCHIVED.value}')",
            name="ck_event_offers_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    level_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("reward_levels.id", ondelete="SET NULL"),
        nullable=True,
    )
    inventory: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    per_user_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventOfferStatus.DRAFT.value,
    )
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    event: Mapped["Event"] = relationship(
        "Event",
        lazy="selectin",
        back_populates="offers",
    )
    required_level: Mapped[Optional["RewardLevel"]] = relationship(
        "RewardLevel",
        back_populates="offers",
        lazy="selectin",
    )
    claims: Mapped[List["EventOfferClaim"]] = relationship(
        "EventOfferClaim",
        back_populates="offer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

