from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_session
from app.users.controllers.user_ticket_controller import UserTicketController
from app.users.schemas.user_ticket_schemas import (
    UserTicketListResponse,
    UserTicketDetailResponse,
)
from app.auth.models import User

router = APIRouter(prefix="/api/users/{user_id}/tickets", tags=["User Tickets"])


@router.get("", response_model=UserTicketListResponse)
async def list_user_tickets(
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserTicketController(session)
    result = await controller.list_user_tickets(user_id, page, page_size)

    return {
        "success": True,
        "data": {
            "items": result["items"],
            "pagination": {
                "page": result["page"],
                "page_size": result["page_size"],
                "total": result["total"],
                "pages": result["pages"],
                "has_next": result.get("has_next", False),
            }
        }
    }


@router.get("/{ticket_id}", response_model=UserTicketDetailResponse)
async def get_ticket_detail(
        user_id: str,
        ticket_id: str,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    controller = UserTicketController(session)
    detail = await controller.get_ticket_detail(user_id, ticket_id)

    return {"success": True, "data": detail}


def get_user_ticket_router():
    return router