from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.common import success_response
from app.tickets.controllers.ticket_controller import TicketController
from app.tickets.dependencies import get_ticket_controller
from app.tickets.schemas.ticket_purchase import TicketPurchaseRequest, TicketPurchaseResponse


def get_ticket_router() -> APIRouter:
    router = APIRouter(prefix="/api/tickets", tags=["tickets"])

    @router.post("/purchase", response_model=dict)
    async def purchase_ticket(
        request: TicketPurchaseRequest,
        current_user: User = Depends(get_current_user),
        controller: TicketController = Depends(get_ticket_controller),
    ):
        """Purchase a ticket for an event."""
        result = await controller.purchase_ticket(request, current_user.id)
        return success_response(result.model_dump(), message=result.message)

    @router.get("/{ticket_id}/pdf")
    async def get_ticket_pdf(
        ticket_id: str,
        current_user: User = Depends(get_current_user),
        controller: TicketController = Depends(get_ticket_controller),
    ):
        """Get ticket PDF."""
        pdf_buffer = await controller.generate_pdf(ticket_id, current_user.id)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ticket-{ticket_id}.pdf"}
        )

    return router

