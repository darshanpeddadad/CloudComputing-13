from fastapi import HTTPException, status
from typing import List

from app.resale.services.resale_service import ResaleService
from app.resale.schemas import (
    TicketResaleListingCreate,
    TicketResaleListingResponse,
    TicketResaleOfferCreate,
    TicketResaleOfferResponse
)

class ResaleController:
    def __init__(self, service: ResaleService):
        self._service = service

    async def create_listing(self, payload: TicketResaleListingCreate, seller_id: str) -> TicketResaleListingResponse:
        try:
            listing = await self._service.create_listing(payload, seller_id)
            return self._service.serialize_listing(listing)
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            # Catch-all for other validation/unexpected errors to avoid 500s
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Listing failed: {str(e)}")

    async def get_active_listings(self) -> List[TicketResaleListingResponse]:
        return await self._service.get_active_listings()

    async def purchase_listing(self, listing_id: str, buyer_id: str) -> TicketResaleListingResponse:
        try:
            listing = await self._service.purchase_listing(listing_id, buyer_id)
            # Re-fetch with eager loading so event/images are available for serialization
            refreshed = await self._service.get_listing_with_details(listing_id)
            return self._service.serialize_listing(refreshed or listing)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def create_offer(self, listing_id: str, payload: TicketResaleOfferCreate, buyer_id: str) -> TicketResaleOfferResponse:
        try:
            offer = await self._service.create_offer(listing_id, payload, buyer_id)
            return TicketResaleOfferResponse.model_validate(offer)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            
    async def accept_offer(self, offer_id: str, seller_id: str) -> TicketResaleOfferResponse:
        try:
            offer = await self._service.accept_offer(offer_id, seller_id)
            return TicketResaleOfferResponse.model_validate(offer)
        except PermissionError as e:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def cancel_listing(self, listing_id: str, seller_id: str) -> TicketResaleListingResponse:
        try:
            listing = await self._service.cancel_listing(listing_id, seller_id)
            return self._service.serialize_listing(listing)
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except ValueError as e:
            message = str(e)
            status_code = status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
            raise HTTPException(status_code=status_code, detail=message)
