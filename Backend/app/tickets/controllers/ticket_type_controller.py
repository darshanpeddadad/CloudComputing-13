from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.auth.models import User
from app.tickets.schemas import (
    TicketTypeCreateRequest,
    TicketTypeUpdateRequest,
    TicketTypeResponse,
)
from app.tickets.services.ticket_service import TicketService


class TicketTypeController:
    """Handles ticket type management operations."""

    def __init__(self, service: TicketService):
        self._service = service

    async def create_ticket_type(
        self,
        event_id: str,
        request: TicketTypeCreateRequest,
        user: User,
    ) -> TicketTypeResponse:
        try:
            ticket_type = await self._service.create_ticket_type(event_id, request, user)
            await self._service._session.commit()
            return TicketTypeResponse.model_validate(ticket_type)
        except PermissionError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=404, detail=str(exc))
        except IntegrityError:
            await self._service._session.rollback()
            raise HTTPException(status_code=400, detail="Ticket type name must be unique per event.")
        except HTTPException:
            await self._service._session.rollback()
            raise
        except Exception as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create ticket type: {str(exc)}")

    async def list_ticket_types(
        self,
        event_id: str,
    ) -> list[TicketTypeResponse]:
        try:
            ticket_types = await self._service.list_ticket_types(event_id)
            return [TicketTypeResponse.model_validate(tt) for tt in ticket_types]
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to fetch ticket types: {str(exc)}")

    async def update_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        payload: TicketTypeUpdateRequest,
        user: User,
    ) -> TicketTypeResponse:
        try:
            ticket_type = await self._service.update_ticket_type(event_id, ticket_type_id, payload, user)
            await self._service._session.commit()
            return TicketTypeResponse.model_validate(ticket_type)
        except PermissionError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=404, detail=str(exc))
        except IntegrityError:
            await self._service._session.rollback()
            raise HTTPException(status_code=400, detail="Ticket type name must be unique per event.")
        except HTTPException:
            await self._service._session.rollback()
            raise
        except Exception as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update ticket type: {str(exc)}")

    async def delete_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        user: User,
    ) -> None:
        try:
            await self._service.delete_ticket_type(event_id, ticket_type_id, user)
            await self._service._session.commit()
        except PermissionError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            await self._service._session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete ticket type: {str(exc)}")

    async def get_ticket_type(
        self,
        event_id: str,
        ticket_type_id: str,
        user: User,
    ) -> TicketTypeResponse:
        try:
            ticket_type = await self._service.get_ticket_type(event_id, ticket_type_id, user)
            return TicketTypeResponse.model_validate(ticket_type)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to fetch ticket type: {str(exc)}")
