from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from .chat_message import ChatMessage


class MessageRead(Base):
    __tablename__ = "message_reads"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_message_reads_message_user",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        back_populates="read_receipts",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship("User", lazy="selectin")

