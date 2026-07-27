from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
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
    from .chat_room import ChatRoom


class ChatParticipantRole(str, Enum):
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    OWNER = "owner"


class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_chat_participants_room_user",
        ),
        CheckConstraint(
            f"role in ('{ChatParticipantRole.PARTICIPANT.value}', "
            f"'{ChatParticipantRole.MODERATOR.value}', '{ChatParticipantRole.OWNER.value}')",
            name="ck_chat_participants_role_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChatParticipantRole.PARTICIPANT.value,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notifications_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    room: Mapped["ChatRoom"] = relationship(
        "ChatRoom",
        back_populates="participants",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")

