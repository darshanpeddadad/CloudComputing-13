from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.events.models import Event
from app.events.schemas import EventCategorySchema, EventOrganizerSchema, EventResponse
from app.tickets.models import Ticket, TicketStatus, TicketTransaction
from app.tickets.models.ticket_transaction import TicketTransactionType
from app.resale.models.ticket_resale_listing import TicketResaleListing, TicketResaleStatus
from app.resale.models.ticket_resale_offer import TicketResaleOffer, TicketResaleOfferStatus
from app.resale.schemas import (
    TicketResaleListingCreate,
    TicketResaleListingResponse,
    TicketResaleOfferCreate,
)

class ResaleService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_listing(self, payload: TicketResaleListingCreate, seller_id: str) -> TicketResaleListing:
       
        ticket = await self._session.get(Ticket, payload.ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")
        
  
        if ticket.owner_id != seller_id:
            raise PermissionError("You do not own this ticket")
            
 
        if not ticket.ticket_type.resale_allowed:
             raise ValueError("Resale is not allowed for this ticket type")


        if ticket.status != TicketStatus.ISSUED:
            raise ValueError(f"Ticket cannot be resold in status {ticket.status}")

      
        stmt = select(TicketResaleListing).where(
            TicketResaleListing.ticket_id == ticket.id,
            TicketResaleListing.status.in_([TicketResaleStatus.ACTIVE, TicketResaleStatus.RESERVED])
        )
        existing = (await self._session.scalars(stmt)).first()
        if existing:
            raise ValueError("Ticket is already listed for resale")


        listing = TicketResaleListing(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            seller_id=seller_id,
            asking_price=payload.asking_price,
            currency=payload.currency,
            allow_offers=payload.allow_offers,
            auto_accept_price=payload.auto_accept_price,
            expires_at=payload.expires_at,
            notes=payload.notes,
            status=TicketResaleStatus.ACTIVE.value
        )
       
        ticket.status = TicketStatus.LISTED.value
        self._session.add(listing)
        await self._session.flush()
        await self._session.refresh(listing)
        return listing

    async def get_active_listings(self) -> List[TicketResaleListingResponse]:
        stmt = (
            select(TicketResaleListing)
            .where(TicketResaleListing.status == TicketResaleStatus.ACTIVE)
            .options(
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.category),
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.organizer),
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.images),
            )
            .order_by(TicketResaleListing.created_at.desc())
        )
        listings = list((await self._session.scalars(stmt)).all())
        return [self._build_listing_response(listing) for listing in listings]

    async def get_listing(self, listing_id: str) -> Optional[TicketResaleListing]:
        return await self._session.get(TicketResaleListing, listing_id)

    async def get_listing_with_details(self, listing_id: str) -> Optional[TicketResaleListing]:
        """Fetch a single listing with all relations eagerly loaded (safe to serialize after commit)."""
        stmt = (
            select(TicketResaleListing)
            .where(TicketResaleListing.id == listing_id)
            .options(
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.category),
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.organizer),
                selectinload(TicketResaleListing.ticket)
                .selectinload(Ticket.event)
                .selectinload(Event.images),
            )
        )
        return (await self._session.scalars(stmt)).first()

    async def purchase_listing(self, listing_id: str, buyer_id: str) -> TicketResaleListing:
        # Use selectinload so listing.ticket is eagerly loaded (prevents async lazy-load greenlet error)
        stmt = (
            select(TicketResaleListing)
            .where(TicketResaleListing.id == listing_id)
            .options(
                selectinload(TicketResaleListing.ticket),
            )
        )
        listing = (await self._session.scalars(stmt)).first()
        if not listing:
            raise ValueError("Listing not found")
        
        if listing.status != TicketResaleStatus.ACTIVE:
            raise ValueError("Listing is not active")
        
        if listing.seller_id == buyer_id:
            raise ValueError("Cannot purchase your own listing")

       
        return await self._execute_sale(listing, buyer_id, listing.asking_price)

    async def create_offer(self, listing_id: str, payload: TicketResaleOfferCreate, buyer_id: str) -> TicketResaleOffer:
        listing = await self._session.get(TicketResaleListing, listing_id)
        if not listing:
            raise ValueError("Listing not found")
            
        if not listing.allow_offers:
            raise ValueError("Offsets are not allowed for this listing")
            
        if listing.seller_id == buyer_id:
             raise ValueError("Cannot offer on your own listing")

        offer = TicketResaleOffer(
            id=str(uuid.uuid4()),
            listing_id=listing_id,
            buyer_id=buyer_id,
            offered_price=payload.offered_price,
            message=payload.message,
            status=TicketResaleOfferStatus.PENDING.value
        )
        self._session.add(offer)
        await self._session.flush()
        await self._session.refresh(offer)
        return offer
        
    async def accept_offer(self, offer_id: str, seller_id: str) -> TicketResaleOffer:
        offer = await self._session.get(TicketResaleOffer, offer_id)
        if not offer:
            raise ValueError("Offer not found")
            
        listing = await self._session.get(TicketResaleListing, offer.listing_id)
        if listing.seller_id != seller_id:
             raise PermissionError("Not authorized to accept details for this listing")
             
        if offer.status != TicketResaleOfferStatus.PENDING:
            raise ValueError("Offer is not pending")
            
    
        await self._execute_sale(listing, offer.buyer_id, offer.offered_price)
        
        offer.status = TicketResaleOfferStatus.ACCEPTED.value
        offer.responded_at = datetime.utcnow()
        await self._session.flush()
        return offer

    async def _execute_sale(self, listing: TicketResaleListing, buyer_id: str, amount: float) -> TicketResaleListing:
        try:
            listing.status = TicketResaleStatus.SOLD.value
            listing.buyer_id = buyer_id
            listing.sale_completed_at = datetime.utcnow()
            
            # ticket is already eagerly loaded via the selectinload relationship
            ticket = listing.ticket
            ticket.owner_id = buyer_id
            ticket.status = TicketStatus.ISSUED.value
            
            txn = TicketTransaction(
                id=str(uuid.uuid4()),
                ticket_id=ticket.id,
                event_id=ticket.event_id,
                buyer_id=buyer_id,
                seller_id=listing.seller_id,
                transaction_type=TicketTransactionType.RESALE.value,
                amount=amount,
                notes=f"Resale listing {listing.id}"
            )
            self._session.add(txn)
            
            from app.chat.services.chat_service import ChatService
            from app.chat.models import ChatParticipantRole
            from app.events.models import Event
            
            chat_service = ChatService(self._session)
            event = await self._session.get(Event, ticket.event_id)
            seller = await self._session.get(User, listing.seller_id)
            buyer = await self._session.get(User, buyer_id)
            
            if event and seller and buyer:
                 try:
                    room = await chat_service.ensure_event_group_room(event, seller) 
                  
                    # Check if seller still holds any tickets for this event
                    from sqlalchemy import select as sa_select, func
                    from app.tickets.models import Ticket as TicketModel, TicketStatus as TicketStatusEnum
                    
                    count_stmt = sa_select(func.count(TicketModel.id)).where(
                        TicketModel.event_id == event.id,
                        TicketModel.owner_id == seller.id,
                        TicketModel.status.in_([
                            TicketStatusEnum.ISSUED.value, 
                            TicketStatusEnum.CHECKED_IN.value, 
                            TicketStatusEnum.LISTED.value
                        ])
                    )
                    remaining_tickets = await self._session.scalar(count_stmt)
                    
                    # Only remove seller from the chat if they have no tickets left
                    if remaining_tickets == 0:
                        await chat_service.remove_participant(room, seller)
                  
                    await chat_service.ensure_participant(room, buyer, ChatParticipantRole.PARTICIPANT)
                 except Exception as chat_err:
                    logger.warning(f"Chat update failed during resale (non-fatal): {chat_err}")

            await self._session.commit()
            return listing
        except Exception as e:
            import traceback
            logger.error(f"_execute_sale failed: {e}\n{traceback.format_exc()}")
            raise

    def serialize_listing(self, listing: TicketResaleListing) -> TicketResaleListingResponse:
        """Convert a listing ORM object into an API-ready response with event details."""
        return self._build_listing_response(listing)

    def _build_listing_response(self, listing: TicketResaleListing) -> TicketResaleListingResponse:
        response = TicketResaleListingResponse.model_validate(listing)
        event_response = self._build_event_response(listing)
        if event_response:
            response = response.model_copy(update={"event": event_response})
        return response

    def _build_event_response(self, listing: TicketResaleListing) -> Optional[EventResponse]:
        ticket = listing.ticket
        event = ticket.event if ticket else None
        if not event or not event.category or not event.organizer:
            return None

        organizer_name = f"{event.organizer.first_names} {event.organizer.last_name}".strip()
        images = sorted(event.images, key=lambda img: (img.position, img.id)) if event.images else []

        return EventResponse(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            latitude=event.latitude,
            longitude=event.longitude,
            start_date=event.start_date,
            end_date=event.end_date,
            start_time=event.start_time,
            end_time=event.end_time,
            sos_enabled=event.sos_enabled,
            status=event.status,
            max_attendees=event.max_attendees,
            category=EventCategorySchema(id=event.category.id, name=event.category.name),
            organizer=EventOrganizerSchema(id=event.organizer.id, name=organizer_name),
            images=[image.url for image in images],
        )

    async def cancel_listing(self, listing_id: str, seller_id: str) -> TicketResaleListing:
        listing = await self._session.get(TicketResaleListing, listing_id)
        if not listing:
            raise ValueError("Listing not found")

        if listing.seller_id != seller_id:
            raise PermissionError("You do not own this listing")

        if listing.status in (
            TicketResaleStatus.SOLD.value,
            TicketResaleStatus.CANCELLED.value,
            TicketResaleStatus.EXPIRED.value,
        ):
            raise ValueError(f"Cannot cancel a listing in status {listing.status}")

        listing.status = TicketResaleStatus.CANCELLED.value
        listing.updated_at = datetime.utcnow()
        ticket = await self._session.get(Ticket, listing.ticket_id)
        if ticket:
            ticket.status = TicketStatus.ISSUED.value

        await self._session.commit()
        await self._session.refresh(listing)
        return listing
