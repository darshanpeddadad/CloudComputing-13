from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.utils import is_admin
from app.common import SuccessResponse, success_response
from app.events.controllers import EventController, get_event_controller
from app.events.schemas import PaginatedEventsResponse

router = APIRouter(prefix="/api/users/{user_id}/events", tags=["User Events"])


@router.get("", response_model=SuccessResponse[PaginatedEventsResponse])
async def list_user_events(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    controller: EventController = Depends(get_event_controller),
):
    if not (is_admin(current_user) or current_user.id == user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    events = await controller.list_organizer_events(user_id, page, page_size)
    return success_response(events)


def get_user_event_router():
    return router
