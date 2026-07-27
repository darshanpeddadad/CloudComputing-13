from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Header, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.auth.dependencies import get_current_user, require_admin
from app.events.schemas.event_create import EventCreateDTO
from app.common import SuccessResponse, success_response
from app.events.controllers import EventController, get_event_controller
from app.events.schemas import (
    EventEditRequestCreate,
    EventEditRequestResponse,
    EventEditRequestReview,
    EventListQuery,
    EventResponse,
    PaginatedEventEditRequestsResponse,
    PaginatedEventsResponse,
)
from app.auth.models import User
from app.auth.utils import user_from_token
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.tickets.controllers.ticket_type_controller import TicketTypeController
from app.tickets.dependencies import get_ticket_type_controller
from app.tickets.schemas import (
    TicketTypeCreateRequest,
    TicketTypeUpdateRequest,
    TicketTypeResponse,
)


def get_event_router() -> APIRouter:
    router = APIRouter(prefix="/api/events", tags=["events"])

    # Custom dependency for event creation that returns custom 401 format
    async def get_current_user_for_event_creation(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """Get current user for event creation, with custom 401 error format."""
        from jose import JWTError
        
        try:
            user = await user_from_token(session, authorization)
        except JWTError:
            user = None
        if user:
            return user
        # Return custom 401 format by raising HTTPException that will be caught
        # We'll handle this in the exception handler, but for now return JSONResponse directly
        from fastapi.responses import JSONResponse as FastAPIJSONResponse
        raise HTTPException(
            status_code=401,
            detail={"success": False, "message": "Not authenticated."}
        )

    # Upload event image (Deprecated - use create_event with multipart/form-data)
    # @router.post("/upload-image", response_model=SuccessResponse[dict])
    # async def upload_image(
    #     file: UploadFile = File(...),
    #     current_user: User = Depends(get_current_user_for_event_creation),
    # ):
    #     from app.common.services.s3_service import s3_service
    #     url = s3_service.upload_file(file, folder="events")
    #     return success_response({"url": url}, message="Image uploaded successfully")

    # Upload multiple event images (Deprecated - use create_event with multipart/form-data)
    # @router.post("/upload-images", response_model=SuccessResponse[dict])
    # async def upload_images(
    #     files: list[UploadFile] = File(...),
    #     current_user: User = Depends(get_current_user_for_event_creation),
    # ):
    #     from app.common.services.s3_service import s3_service
    #     urls = []
    #     for file in files:
    #         url = s3_service.upload_file(file, folder="events")
    #         urls.append(url)
    #     return success_response({"urls": urls}, message="Images uploaded successfully")

    # List of public events
    @router.get("/", response_model=SuccessResponse[PaginatedEventsResponse])
    async def list_events(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        category: Optional[str] = Query(default=None),
        search: Optional[str] = Query(default=None),
        location: Optional[str] = Query(default=None),
        start_date_from: Optional[date] = Query(default=None),
        start_date_to: Optional[date] = Query(default=None),
        min_attendees: Optional[int] = Query(default=None, ge=1),
        max_attendees: Optional[int] = Query(default=None, ge=1),
        time_filter: Optional[str] = Query(default=None),
        sort_by: str = Query(default="start_date_asc"),
        use_semantic_search: bool = Query(default=False),
        controller: EventController = Depends(get_event_controller),
    ):
        query = EventListQuery(
            page=page,
            page_size=page_size,
            category=category,
            search=search,
            location=location,
            start_date_from=start_date_from,
            start_date_to=start_date_to,
            min_attendees=min_attendees,
            max_attendees=max_attendees,
            time_filter=time_filter,
            sort_by=sort_by,
            use_semantic_search=use_semantic_search,
        )
        result = await controller.list_events(query)
        return success_response(result)


    # create event
    @router.post("/", status_code=201)
    async def create_event(
        event_data: str = Form(...),
        images: list[UploadFile] = File(default=[]),
        controller: EventController = Depends(get_event_controller),
        current_user: User = Depends(get_current_user_for_event_creation),
    ):
        import json
        try:
            payload_dict = json.loads(event_data)
            payload = EventCreateDTO(**payload_dict)
        except json.JSONDecodeError:
             raise HTTPException(status_code=400, detail="Invalid JSON format in event_data")
        except Exception as e:
             raise HTTPException(status_code=422, detail=str(e))

        event = await controller.create_event(payload, current_user, images)
        return success_response(
            {
                "id": event.id,
                "title": event.title,
                "status": event.status,
                "category": {"id": event.category.id, "name": event.category.name},
                "organizer": {"id": event.organizer.id},
                "images": [img.url for img in event.images],
            },
            message="Event created successfully",
        )

    # create ticket type for an event
    @router.post(
        "/{event_id}/ticket-types",
        status_code=201,
        response_model=SuccessResponse[TicketTypeResponse],
    )
    async def create_ticket_type(
        event_id: str,
        payload: TicketTypeCreateRequest,
        controller: TicketTypeController = Depends(get_ticket_type_controller),
        current_user: User = Depends(get_current_user),
    ):
        ticket_type = await controller.create_ticket_type(event_id, payload, current_user)
        return success_response(ticket_type, message="Ticket type created successfully")

    @router.get(
        "/{event_id}/ticket-types",
        response_model=SuccessResponse[list[TicketTypeResponse]],
    )
    async def list_ticket_types(
        event_id: str,
        controller: TicketTypeController = Depends(get_ticket_type_controller),
    ):
        ticket_types = await controller.list_ticket_types(event_id)
        return success_response(ticket_types, message="Ticket types fetched successfully")

    @router.patch(
        "/{event_id}/ticket-types/{ticket_type_id}",
        response_model=SuccessResponse[TicketTypeResponse],
    )
    async def update_ticket_type(
        event_id: str,
        ticket_type_id: str,
        payload: TicketTypeUpdateRequest,
        controller: TicketTypeController = Depends(get_ticket_type_controller),
        current_user: User = Depends(get_current_user),
    ):
        ticket_type = await controller.update_ticket_type(event_id, ticket_type_id, payload, current_user)
        return success_response(ticket_type, message="Ticket type updated successfully")

    @router.delete(
        "/{event_id}/ticket-types/{ticket_type_id}",
        response_model=SuccessResponse[dict],
    )
    async def delete_ticket_type(
        event_id: str,
        ticket_type_id: str,
        controller: TicketTypeController = Depends(get_ticket_type_controller),
        current_user: User = Depends(get_current_user),
    ):
        await controller.delete_ticket_type(event_id, ticket_type_id, current_user)
        return success_response({}, message="Ticket type deleted successfully")

    @router.get(
        "/{event_id}/ticket-types/{ticket_type_id}",
        response_model=SuccessResponse[TicketTypeResponse],
    )
    async def get_ticket_type(
        event_id: str,
        ticket_type_id: str,
        controller: TicketTypeController = Depends(get_ticket_type_controller),
        current_user: User = Depends(get_current_user),
    ):
        ticket_type = await controller.get_ticket_type(event_id, ticket_type_id, current_user)
        return success_response(ticket_type, message="Ticket type fetched successfully")

    # list of pending events
    @router.get("/pending", response_model=SuccessResponse[PaginatedEventsResponse])
    async def list_pending_events(
            page: int = Query(1, ge=1),
            page_size: int = Query(10, ge=1, le=50),
            category: Optional[str] = Query(default=None),
            search: Optional[str] = Query(default=None),
            location: Optional[str] = Query(default=None),
            start_date_from: Optional[date] = Query(default=None),
            start_date_to: Optional[date] = Query(default=None),
            min_attendees: Optional[int] = Query(default=None, ge=1),
            max_attendees: Optional[int] = Query(default=None, ge=1),
            time_filter: Optional[str] = Query(default=None),
            sort_by: str = Query(default="start_date_asc"),
            use_semantic_search: bool = Query(default=False),
            current_user=Depends(require_admin),  # Admin only access
            controller: EventController = Depends(get_event_controller),
    ):
        query = EventListQuery(
            page=page,
            page_size=page_size,
            category=category,
            search=search,
            location=location,
            start_date_from=start_date_from,
            start_date_to=start_date_to,
            min_attendees=min_attendees,
            max_attendees=max_attendees,
            time_filter=time_filter,
            sort_by=sort_by,
            use_semantic_search=use_semantic_search,
        )
        result = await controller.list_pending_events(query)
        return success_response(result, message="Pending events fetched successfully")

    @router.post(
        "/{event_id}/edit-requests",
        response_model=SuccessResponse[EventEditRequestResponse],
    )
    async def create_event_edit_request(
        event_id: str,
        payload: EventEditRequestCreate,
        controller: EventController = Depends(get_event_controller),
        current_user: User = Depends(get_current_user),
    ):
        edit_request = await controller.request_event_edit(event_id, payload, current_user)
        return success_response(edit_request, message="Edit request submitted successfully")

    @router.get(
        "/edit-requests",
        response_model=SuccessResponse[PaginatedEventEditRequestsResponse],
    )
    async def list_event_edit_requests(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        status: Optional[str] = Query(default=None),
        search: Optional[str] = Query(default=None),
        current_user: User = Depends(require_admin),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.list_event_edit_requests(status, page, page_size, search)
        return success_response(result, message="Event edit requests fetched successfully")

    @router.get(
        "/edit-requests/mine",
        response_model=SuccessResponse[PaginatedEventEditRequestsResponse],
    )
    async def list_my_event_edit_requests(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        status: Optional[str] = Query(default=None),
        search: Optional[str] = Query(default=None),
        current_user: User = Depends(get_current_user),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.list_my_event_edit_requests(
            current_user.id,
            status,
            page,
            page_size,
            search,
        )
        return success_response(result, message="Event edit requests fetched successfully")

    @router.post(
        "/edit-requests/{edit_request_id}/approve",
        response_model=SuccessResponse[EventEditRequestResponse],
    )
    async def approve_event_edit_request(
        edit_request_id: str,
        payload: Optional[EventEditRequestReview] = None,
        current_user: User = Depends(require_admin),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.approve_event_edit_request(edit_request_id, current_user, payload)
        return success_response(result, message="Edit request approved successfully")

    @router.post(
        "/edit-requests/{edit_request_id}/reject",
        response_model=SuccessResponse[EventEditRequestResponse],
    )
    async def reject_event_edit_request(
        edit_request_id: str,
        payload: Optional[EventEditRequestReview] = None,
        current_user: User = Depends(require_admin),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.reject_event_edit_request(edit_request_id, current_user, payload)
        return success_response(result, message="Edit request rejected successfully")

    @router.get(
        "/recommendations",
        response_model=SuccessResponse[PaginatedEventsResponse],
    )
    async def get_recommended_events(
        current_user: User = Depends(get_current_user),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.list_recommended_events(current_user)
        return success_response(result, message="Recommended events fetched successfully")

    # get event details
    @router.get("/{event_id}", response_model=SuccessResponse[EventResponse])
    async def get_event(
        event_id: str,
        controller: EventController = Depends(get_event_controller),
    ):
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        from app.common.responses import error_response
        
        try:
            result = await controller.get_event(event_id)
            return success_response(result)
        except HTTPException as exc:
            if exc.status_code == 404:
                return JSONResponse(
                    status_code=404,
                    content=error_response("Event not found")
                )
            raise

    # delete event
    @router.delete("/{event_id}", status_code=200)
    async def delete_event(
        event_id: str,
        current_user=Depends(get_current_user),
        controller: EventController = Depends(get_event_controller),
    ):
        result = await controller.delete_event(event_id, current_user)
        return result

    # approve event
    @router.post("/{event_id}/approve")
    async def approve_event(
        event_id: str,
        current_user=Depends(require_admin),
        controller: EventController = Depends(get_event_controller),
    ):
        updated_event = await controller.approve_event(event_id, current_user)
        return success_response(updated_event, message="Event approved successfully")

    # rejection of event
    @router.post("/{event_id}/reject")
    async def reject_event(
        event_id: str,
        current_user=Depends(require_admin),
        controller: EventController = Depends(get_event_controller),
    ):
        updated_event = await controller.reject_event(event_id, current_user)
        return success_response(updated_event, message="Event rejected successfully")

    return router
