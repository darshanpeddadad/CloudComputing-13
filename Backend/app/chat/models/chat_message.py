from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .chat_room import ChatRoom
    from .message_read import MessageRead


class ChatMessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
    MEDIA = "media"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    room_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_message_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    message_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChatMessageType.TEXT.value,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    room: Mapped["ChatRoom"] = relationship(
        "ChatRoom",
        back_populates="messages",
        lazy="selectin",
    )
    sender: Mapped[Optional["User"]] = relationship("User", lazy="selectin")
    parent_message: Mapped[Optional["ChatMessage"]] = relationship(
        "ChatMessage",
        remote_side="ChatMessage.id",
        lazy="selectin",
    )
    read_receipts: Mapped[List["MessageRead"]] = relationship(
        "MessageRead",
        back_populates="message",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

