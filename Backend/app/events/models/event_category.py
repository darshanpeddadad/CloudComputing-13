from __future__ import annotations

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventCategory(Base):
    __tablename__ = "event_categories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="category",
    )
