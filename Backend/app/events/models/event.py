from __future__ import annotations

import uuid
from datetime import date, time
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.auth.models.user import User
    from app.tickets.models import TicketType, Ticket
    from app.rewards.models import EventParticipation
    from app.offers.models import EventOffer
    from app.chat.models import ChatRoom
    from .event_edit_request import EventEditRequest

from .event_category import EventCategory
from .event_status import EventStatus
from .event_image import EventImage


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'approved', 'rejected')",
            name="ck_events_status_valid",
        ),
    )


    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    sos_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EventStatus.PENDING.value,
    )

    max_attendees: Mapped[int] = mapped_column(Integer, nullable=False)

    organizer_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("event_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped["EventCategory"] = relationship(
        "EventCategory",
        back_populates="events",
        lazy="selectin",
    )

    organizer: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    ticket_types: Mapped[List["TicketType"]] = relationship(
        "TicketType",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    images: Mapped[List["EventImage"]] = relationship(
        "EventImage",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventImage.position",
        lazy="selectin",
    )

    participations: Mapped[List["EventParticipation"]] = relationship(
        "EventParticipation",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    offers: Mapped[List["EventOffer"]] = relationship(
        "EventOffer",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    chat_rooms: Mapped[List["ChatRoom"]] = relationship(
        "ChatRoom",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    edit_requests: Mapped[List["EventEditRequest"]] = relationship(
        "EventEditRequest",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
