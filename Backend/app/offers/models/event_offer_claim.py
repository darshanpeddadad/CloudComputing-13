from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .event_offer import EventOffer


class EventOfferClaimStatus(str, Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REDEEMED = "redeemed"
    EXPIRED = "expired"


class EventOfferClaim(Base):
    __tablename__ = "event_offer_claims"
    __table_args__ = (
        UniqueConstraint(
            "offer_id",
            "user_id",
            name="uq_event_offer_claims_offer_user",
        ),
        CheckConstraint(
            f"status in ('{EventOfferClaimStatus.INVITED.value}', '{EventOfferClaimStatus.ACCEPTED.value}', "
            f"'{EventOfferClaimStatus.DECLINED.value}', '{EventOfferClaimStatus.REDEEMED.value}', "
            f"'{EventOfferClaimStatus.EXPIRED.value}')",
            name="ck_event_offer_claims_status_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    offer_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("event_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventOfferClaimStatus.INVITED.value,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    offer: Mapped["EventOffer"] = relationship(
        "EventOffer",
        back_populates="claims",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")

