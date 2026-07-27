from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.events.models import Event


class EventImage(Base):
    __tablename__ = "event_images"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),   # ⭐ FIX: Generate ID automatically
        nullable=False,
    )

    event_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    url: Mapped[str] = mapped_column(String(500), nullable=False)

    position: Mapped[int] = mapped_column(Integer, nullable=False)

    event: Mapped["Event"] = relationship("Event", back_populates="images")
