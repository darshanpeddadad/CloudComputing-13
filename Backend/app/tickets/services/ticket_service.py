from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Tuple, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tickets.models import Ticket, TicketType, TicketStatus
from app.tickets.repositories import TicketRepository
from app.events.models import Event
from app.events.models.event_status import EventStatus
from app.auth.models import User
from app.chat.services.chat_service import ChatService
from app.chat.models import ChatParticipantRole, ChatRoomType
from app.auth.utils.auth_checks import is_admin
from app.tickets.schemas import TicketTypeCreateRequest, TicketTypeUpdateRequest

if TYPE_CHECKING:
    from app.rewards.services import RewardService
    from app.rewards.schemas import PointAwardResult


class TicketService:
    """Business logic for ticket operations."""

    def __init__(self, session: AsyncSession, repo: TicketRepository):
        self._session = session
        self._repo = repo

    async def purchase_ticket(
        self,
        event_id: str,
        buyer_id: str,
        items: list[dict],
        reward_service: Optional["RewardService"] = None,
        redeem_points: Optional[int] = None,
    ) -> Tuple[list[Ticket], Optional["PointAwardResult"], dict]:
        """
        Purchase tickets for an event.
        
        Returns:
            Tuple of (list of tickets, point_award_result, redemption_info)
        """
        # Validate event exists and is approved
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        
        if event.status != EventStatus.APPROVED.value:
            raise ValueError("Event is not approved")

        if self._event_has_ended(event):
            raise ValueError("Event has already ended")
        
        # Validate buyer exists
        buyer = await self._session.get(User, buyer_id)
        if not buyer:
            raise ValueError("User not found")

        total_price = 0.0
        ticket_types_data = {}

        for item in items:
            ticket_type_id = item["ticket_type_id"]
            quantity = item["quantity"]
            
            # Get or create ticket type
            ticket_type = await self._session.get(TicketType, ticket_type_id)
            if not ticket_type:
                # Create default ticket type if it doesn't exist
                ticket_type = TicketType(
                    id=ticket_type_id,
                    event_id=event_id,
                    name="General Admission",
                    price=0.0,
                    currency="USD",
                    capacity=100,
                    max_per_user=None,
                )
                self._session.add(ticket_type)
                await self._session.flush()
            elif ticket_type.event_id != event_id:
                raise ValueError(f"Ticket type {ticket_type_id} does not belong to this event")
            
            # Validate quantity against max_per_user
            if ticket_type.max_per_user is not None:
                from sqlalchemy import select, func
                stmt = select(func.count(Ticket.id)).where(
                    Ticket.ticket_type_id == ticket_type.id,
                    Ticket.owner_id == buyer_id,
                    Ticket.status != TicketStatus.CANCELLED.value
                )
                current_count = await self._session.scalar(stmt)
                if current_count + quantity > ticket_type.max_per_user:
                    raise ValueError(f"Failed to buy {quantity} ticket(s) of {ticket_type.name}, you have already bought max ticket for this category")

            ticket_types_data[ticket_type_id] = {"type": ticket_type, "quantity": quantity}
            total_price += float(ticket_type.price) * quantity

        # Handle point redemption for discount
        redemption_info = {
            "points_redeemed": 0,
            "discount_applied": 0.0,
            "discount_capped": False,
            "final_price": total_price,
        }
        
        if redeem_points and redeem_points > 0 and reward_service:
            try:
                redemption_result = await reward_service.redeem_points_for_purchase(
                    user_id=buyer_id,
                    points_to_redeem=redeem_points,
                    event_id=event_id,
                    ticket_price=total_price,
                )
                redemption_info["points_redeemed"] = redemption_result.get("points_redeemed", 0)
                redemption_info["discount_applied"] = redemption_result.get("discount_amount", 0.0)
                redemption_info["discount_capped"] = redemption_result.get("discount_capped", False)
                redemption_info["final_price"] = max(
                    0.0, 
                    total_price - redemption_info["discount_applied"]
                )
            except ValueError as e:
                # If redemption fails, continue without discount
                pass
        
        # Create tickets
        tickets = []
        for tt_id, data in ticket_types_data.items():
            t_type = data["type"]
            qty = data["quantity"]
            for _ in range(qty):
                ticket = Ticket(
                    id=str(uuid.uuid4()),
                    ticket_type_id=t_type.id,
                    event_id=event_id,
                    owner_id=buyer_id,
                    status=TicketStatus.ISSUED.value,
                    purchased_at=datetime.utcnow(),
                    original_price=t_type.price,
                )
                self._session.add(ticket)
                tickets.append(ticket)
            
        await self._session.flush()
        
        # Award points for purchase
        point_result = None
        if reward_service:
            try:
                point_result = await reward_service.award_points_for_purchase(
                    user_id=buyer_id,
                    event_id=event_id,
                    ticket_id=tickets[0].id,
                )
            except Exception as e:
                # Don't fail purchase if reward fails
                pass

        # Auto-add buyer to event group chat room (create room if needed)
        try:
            chat_service = ChatService(self._session)
            room = await chat_service.ensure_event_group_room(event, buyer)
            # Ensure organizer present as owner
            if event.organizer:
                await chat_service.ensure_participant(room, event.organizer, ChatParticipantRole.OWNER)
            # Ensure all admins are owners
            admin_stmt = select(User).options(selectinload(User.roles))
            admins = (await self._session.scalars(admin_stmt)).all()
            for admin_user in admins:
                if is_admin(admin_user):
                    await chat_service.ensure_participant(room, admin_user, ChatParticipantRole.OWNER)
            # Add buyer as participant
            await chat_service.ensure_participant(room, buyer, ChatParticipantRole.PARTICIPANT)
            await self._session.commit()
        except Exception:
            # If chat linkage fails, do not fail ticket purchase
            await self._session.rollback()
            raise
        
        return tickets, point_result, redemption_info

    @staticmethod
    def _event_has_ended(event: Event) -> bool:
        end_at = datetime.combine(event.end_date, event.end_time)
        return datetime.utcnow() >= end_at

    async def create_ticket_type(
        self,
        event_id: str,
        payload: TicketTypeCreateRequest,
        user: User,
    ) -> TicketType:
        """Create a ticket type for an event, requiring explicit resale_allowed flag."""
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")

        if not is_admin(user) and event.organizer_id != user.id:
            raise PermissionError("Not authorized to manage ticket types for this event.")

        ticket_type = TicketType(
            id=str(uuid.uuid4()),
            event_id=event_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            capacity=payload.capacity,
            max_per_user=payload.max_per_user,
            resale_allowed=payload.resale_allowed,
            sale_starts_at=payload.sale_starts_at,
            sale_ends_at=payload.sale_ends_at,
        )
        self._session.add(ticket_type)
        await self._session.flush()
        return ticket_type

    async def list_ticket_types(self, event_id: str) -> list[TicketType]:
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")

        stmt = select(TicketType).where(TicketType.event_id == event_id)
        ticket_types = (await self._session.scalars(stmt)).all()
        return list(ticket_types)

    async def update_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        payload: TicketTypeUpdateRequest,
        user: User,
    ) -> TicketType:
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        if not is_admin(user) and event.organizer_id != user.id:
            raise PermissionError("Not authorized to manage ticket types for this event.")

        ticket_type = await self._session.get(TicketType, ticket_type_id)
        if not ticket_type or ticket_type.event_id != event_id:
            raise ValueError("Ticket type not found")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(ticket_type, field, value)

        await self._session.flush()
        return ticket_type

    async def get_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        user: User,
    ) -> TicketType:
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        if not is_admin(user) and event.organizer_id != user.id:
            raise PermissionError("Not authorized to view ticket types for this event.")

        ticket_type = await self._session.get(TicketType, ticket_type_id)
        if not ticket_type or ticket_type.event_id != event_id:
            raise ValueError("Ticket type not found")
        return ticket_type

    async def delete_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        user: User,
    ) -> None:
        event = await self._session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        if not is_admin(user) and event.organizer_id != user.id:
            raise PermissionError("Not authorized to manage ticket types for this event.")

        ticket_type = await self._session.get(TicketType, ticket_type_id)
        if not ticket_type or ticket_type.event_id != event_id:
            raise ValueError("Ticket type not found")

        await self._session.delete(ticket_type)
        await self._session.flush()

    async def get_ticket_by_id(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        stmt = (
            select(Ticket)
            .options(selectinload(Ticket.event))
            .where(Ticket.id == ticket_id)
        )
        return await self._session.scalar(stmt)
    async def get_ticket_pdf_data(self, ticket_id: str, user_id: str) -> tuple[dict, dict, str]:
        """Get data required for generating ticket PDF."""
        # Fetch ticket with related event and owner using repository
        ticket = await self._repo.get_ticket_with_relations(ticket_id)
        
        if not ticket:
            raise ValueError("Ticket not found")
            
        # Check ownership
        if ticket.owner_id != user_id:
             # Ideally check for admin here too, but for now simple ownership check
            raise PermissionError("Not authorized to access this ticket")

        event = ticket.event
        owner = ticket.owner

        event_data = {
            "title": event.title,
            "formatted_date": event.start_date.strftime("%Y-%m-%d"), # Assuming date object
            "location": event.location,
            "price": f"{ticket.original_price} {ticket.event.currency if hasattr(ticket.event, 'currency') else 'USD'}", # fallback
        }

        user_data = {
            "full_name": owner.full_name if hasattr(owner, 'full_name') else owner.email,
        }

        return event_data, user_data, ticket.id
