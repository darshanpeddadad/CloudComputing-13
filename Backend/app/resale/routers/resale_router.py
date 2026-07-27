from fastapi import APIRouter, Depends
from typing import List

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.resale.controllers.resale_controller import ResaleController
from app.resale.dependencies import get_resale_controller
from app.resale.schemas import (
    TicketResaleListingCreate,
    TicketResaleListingResponse,
    TicketResaleOfferCreate,
    TicketResaleOfferResponse
)

def get_resale_router() -> APIRouter:
    router = APIRouter(prefix="/api/resale", tags=["resale"])

    @router.post("/listings", response_model=TicketResaleListingResponse, status_code=201)
    async def create_listing(
        payload: TicketResaleListingCreate,
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.create_listing(payload, current_user.id)

    @router.get(
        "/listings",
        response_model=List[TicketResaleListingResponse],
        summary="List active resale tickets",
        description="Returns all active resale listings including the associated event details.",
    )
    async def get_listings(
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.get_active_listings()

    @router.post("/listings/{listing_id}/purchase", response_model=TicketResaleListingResponse)
    async def purchase_listing(
        listing_id: str,
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.purchase_listing(listing_id, current_user.id)

    @router.post("/listings/{listing_id}/offers", response_model=TicketResaleOfferResponse, status_code=201)
    async def create_offer(
        listing_id: str,
        payload: TicketResaleOfferCreate,
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.create_offer(listing_id, payload, current_user.id)
        
    @router.post("/offers/{offer_id}/accept", response_model=TicketResaleOfferResponse)
    async def accept_offer(
        offer_id: str,
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.accept_offer(offer_id, current_user.id)

    @router.post("/listings/{listing_id}/cancel", response_model=TicketResaleListingResponse)
    async def cancel_listing(
        listing_id: str,
        current_user: User = Depends(get_current_user),
        controller: ResaleController = Depends(get_resale_controller),
    ):
        return await controller.cancel_listing(listing_id, current_user.id)

    return router
