from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.events.models import Event
    from app.auth.models import User
    from .chat_participant import ChatParticipant
    from .chat_message import ChatMessage


class ChatRoomType(str, Enum):
    EVENT_GROUP = "event_group"
    DIRECT = "direct"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        UniqueConstraint("direct_key", name="uq_chat_rooms_direct_key"),
        CheckConstraint(
            f"room_type in ('{ChatRoomType.EVENT_GROUP.value}', '{ChatRoomType.DIRECT.value}')",
            name="ck_chat_rooms_type_valid",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChatRoomType.EVENT_GROUP.value,
    )
    event_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    direct_key: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
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
    topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    event: Mapped[Optional["Event"]] = relationship(
        "Event",
        back_populates="chat_rooms",
        lazy="selectin",
    )
    created_by: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    participants: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

