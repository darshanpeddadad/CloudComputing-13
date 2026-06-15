from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

from app.tickets.models import Ticket, TicketType
from app.events.models import Event
from app.users.schemas.user_ticket_schemas import (
    UserTicketSummary,
    UserTicketDetail,
)


class UserTicketController:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_user_tickets(self, user_id: str, page: int = 1, page_size: int = 10):
        """Return paginated tickets owned by a user."""
        offset = (page - 1) * page_size

        # Query paginated results with ticket type and event data
        stmt = (
            select(Ticket, TicketType, Event)
            .join(TicketType, Ticket.ticket_type_id == TicketType.id)
            .join(Event, Ticket.event_id == Event.id)
            .where(Ticket.owner_id == user_id)
            .order_by(Ticket.purchased_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        rows = (await self.session.execute(stmt)).all()

        tickets = []
        for ticket, ticket_type, event in rows:
            image_url = event.images[0].url if getattr(event, "images", None) else None
            tickets.append(
                UserTicketSummary(
                    ticket_id=ticket.id,
                    ticket_type_id=ticket_type.id,
                    ticket_type=ticket_type.name,
                    ticket_type_description=ticket_type.description,
                    ticket_type_price=float(ticket_type.price) if ticket_type.price is not None else None,
                    ticket_type_currency=ticket_type.currency,
                    resale_allowed=ticket_type.resale_allowed,
                    seat_label=ticket.seat_label,
                    qr_code=ticket.qr_code,
                    metadata=ticket.metadata_json,
                    price=float(ticket.original_price) if ticket.original_price is not None else None,
                    status=ticket.status,
                    purchased_at=ticket.purchased_at,
                    checked_in_at=ticket.checked_in_at,
                    cancelled_at=ticket.cancelled_at,
                    event_id=event.id,
                    event_name=event.title,
                    event_description=event.description,
                    event_location=event.location,
                    event_date=str(event.start_date) if event.start_date else None,
                    event_time=str(event.start_time) if event.start_time else None,
                    event_end_date=str(event.end_date) if event.end_date else None,
                    event_end_time=str(event.end_time) if event.end_time else None,
                    event_image=image_url,
                )
            )

        # Count total - OPTIMIZED with scalar query
        count_stmt = select(func.count(Ticket.id)).where(Ticket.owner_id == user_id)
        total = await self.session.scalar(count_stmt)

        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages

        return {
            "items": tickets,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": total_pages,
            "has_next": has_next,
        }

    async def get_ticket_detail(self, user_id: str, ticket_id: str):
        """Return detailed information for one specific ticket."""
        stmt = (
            select(Ticket, TicketType, Event)
            .join(TicketType, Ticket.ticket_type_id == TicketType.id)
            .join(Event, Ticket.event_id == Event.id)
            .where(Ticket.id == ticket_id, Ticket.owner_id == user_id)
        )

        row = (await self.session.execute(stmt)).first()

        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket, ticket_type, event = row
        image_url = event.images[0].url if getattr(event, "images", None) else None

        return UserTicketDetail(
            ticket_id=ticket.id,
            ticket_type_id=ticket_type.id,
            ticket_type=ticket_type.name,
            ticket_type_description=ticket_type.description,
            ticket_type_price=float(ticket_type.price) if ticket_type.price is not None else None,
            ticket_type_currency=ticket_type.currency,
            resale_allowed=ticket_type.resale_allowed,
            seat_label=ticket.seat_label,
            qr_code=ticket.qr_code,
            metadata=ticket.metadata_json,
            price=float(ticket.original_price) if ticket.original_price is not None else None,
            status=ticket.status,
            purchased_at=ticket.purchased_at,
            checked_in_at=ticket.checked_in_at,
            cancelled_at=ticket.cancelled_at,
            event_id=event.id,
            event_name=event.title,
            event_description=event.description,
            event_location=event.location,
            event_date=str(event.start_date) if event.start_date else None,
            event_time=str(event.start_time) if event.start_time else None,
            event_end_date=str(event.end_date) if event.end_date else None,
            event_end_time=str(event.end_time) if event.end_time else None,
            event_image=image_url,
        )

