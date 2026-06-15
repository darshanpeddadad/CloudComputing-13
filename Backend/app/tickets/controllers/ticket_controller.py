from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from fastapi import HTTPException

from app.tickets.services.ticket_service import TicketService
from app.tickets.schemas.ticket_purchase import TicketPurchaseRequest, TicketPurchaseResponse

if TYPE_CHECKING:
    from app.auth.models import User
    from app.rewards.services import RewardService
from app.chat.services.chat_service import ChatService
from app.chat.models import ChatParticipantRole
import io
from app.tickets.services.pdf_service import PDFService


class TicketController:
    """Coordinates request handling for tickets."""

    def __init__(self, service: TicketService, reward_service: Optional["RewardService"] = None):
        self._service = service
        self._reward_service = reward_service

    async def purchase_ticket(self, request: TicketPurchaseRequest, buyer_id: str) -> TicketPurchaseResponse:
        """Purchase tickets from a cart with optional point redemption and auto-award points."""
        try:
            # Build list of items
            items = [{"ticket_type_id": item.ticket_type_id, "quantity": item.quantity} for item in request.items]
            if request.ticket_type_id:
                items.append({"ticket_type_id": request.ticket_type_id, "quantity": request.quantity})
                
            if not items:
                raise ValueError("No tickets selected for purchase")

            tickets, point_result, redemption_info = await self._service.purchase_ticket(
                event_id=request.event_id,
                buyer_id=buyer_id,
                items=items,
                reward_service=self._reward_service,
                redeem_points=request.redeem_points,
            )
            
            response = TicketPurchaseResponse(
                ticket_id=tickets[0].id,
                ticket_ids=[t.id for t in tickets],
                event_id=tickets[0].event_id,
                status=tickets[0].status,
                message="Ticket purchased successfully",
                # Redemption info
                points_redeemed=redemption_info.get("points_redeemed", 0),
                discount_applied=redemption_info.get("discount_applied", 0.0),
                final_price=redemption_info.get("final_price", 0.0),
            )
            
            # Add point award info
            if point_result:
                response.points_awarded = point_result.points_awarded
                response.new_point_balance = point_result.new_balance
                response.badge_upgraded = point_result.badge_upgraded
                if point_result.new_badge:
                    response.new_badge_name = point_result.new_badge.name
                if point_result.points_awarded > 0:
                    response.message = f"Ticket purchased! You earned {point_result.points_awarded} points."
            
            return response
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to purchase ticket: {str(e)}")

    async def generate_pdf(self, ticket_id: str, user_id: str) -> io.BytesIO:
        """Generates a PDF for the given ticket."""
        try:
            event_data, user_data, booking_id = await self._service.get_ticket_pdf_data(ticket_id, user_id)
            return PDFService.generate_ticket_pdf(event_data, user_data, booking_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

