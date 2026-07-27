from __future__ import annotations

from datetime import date, time
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.common.pagination import PaginationMeta, build_pagination_meta
from app.events.models import Event, EventEditRequest, EventEditRequestStatus, EventStatus
from app.auth.utils import is_admin, is_admin_or_owner
from app.events.repositories import EventRepository
from app.events.schemas import (
    EventCategorySchema,
    EventEditRequestCreate,
    EventEditRequestResponse,
    EventEditRequestReview,
    EventListQuery,
    EventOrganizerSchema,
    EventResponse,
    PaginatedEventEditRequestsResponse,
    PaginatedEventsResponse,
)
from app.common.services.chroma_service import chroma_service


class EventService:
    """Business logic for querying events."""

    def __init__(self, repository: EventRepository):
        self._repository = repository

    _editable_fields = {
        "title",
        "description",
        "location",
        "latitude",
        "longitude",
        "category_id",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "max_attendees",
        "sos_enabled",
    }
    _date_fields = {"start_date", "end_date"}
    _time_fields = {"start_time", "end_time"}
    _int_fields = {"max_attendees"}
    _float_fields = {"latitude", "longitude"}
    _field_parsers = {
        **{field: date.fromisoformat for field in _date_fields},
        **{field: time.fromisoformat for field in _time_fields},
        **{field: int for field in _int_fields},
        **{field: float for field in _float_fields},
    }

    async def list_public_events(self, query: EventListQuery) -> PaginatedEventsResponse:
        if query.search and query.use_semantic_search:
            semantic_ids = await chroma_service.search_events_semantically(query.search)
            query.semantic_event_ids = semantic_ids
            
        events, total = await self._repository.list_public_events(query)
        pagination = build_pagination_meta(query.page, query.page_size, total)
        return PaginatedEventsResponse(
            items=[self._serialize_event(event) for event in events],
            pagination=pagination
        )

    def _serialize_event(self, event: Event) -> EventResponse:
        organizer_name = f"{event.organizer.first_names} {event.organizer.last_name}".strip()
        image_urls = [image.url for image in sorted(event.images, key=lambda img: (img.position, img.id))]
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
            images=image_urls,
        )

    def _serialize_user(self, user) -> Optional[EventOrganizerSchema]:
        if not user:
            return None
        name = f"{user.first_names} {user.last_name}".strip()
        return EventOrganizerSchema(id=user.id, name=name)

    def _serialize_change_value(self, value: Any) -> Any:
        if isinstance(value, (date, time)):
            return value.isoformat()
        return value

    def _parse_change_value(self, field: str, value: Any) -> Any:
        if value is None:
            return None
        parser = self._field_parsers.get(field)
        if not parser:
            return value
        if field in self._date_fields and isinstance(value, date):
            return value
        if field in self._time_fields and isinstance(value, time):
            return value
        return parser(value)
        return value

    def _build_event_edit_changes(self, event: Event, updates: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        changes: Dict[str, Dict[str, Any]] = {}
        for field, new_value in updates.items():
            if field not in self._editable_fields:
                continue
            current_value = getattr(event, field)
            if current_value != new_value:
                changes[field] = {
                    "from": self._serialize_change_value(current_value),
                    "to": self._serialize_change_value(new_value),
                }
        return changes

    def _extract_updates_from_changes(self, changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        for field, change in changes.items():
            if field not in self._editable_fields:
                continue
            updates[field] = self._parse_change_value(field, change.get("to"))
        return updates

    def _assert_event_matches_changes(self, event: Event, changes: Dict[str, Dict[str, Any]]) -> None:
        for field, change in changes.items():
            if field not in self._editable_fields:
                continue
            current_value = getattr(event, field)
            if self._serialize_change_value(current_value) != change.get("from"):
                raise HTTPException(
                    status_code=409,
                    detail="Event changed since edit request was created.",
                )

    def _validate_event_schedule(self, event: Event, updates: Dict[str, Any]) -> None:
        start_date = updates.get("start_date", event.start_date)
        end_date = updates.get("end_date", event.end_date)
        start_time = updates.get("start_time", event.start_time)
        end_time = updates.get("end_time", event.end_time)

        if end_date < start_date:
            raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
        if start_date == end_date and end_time <= start_time:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")

        if "max_attendees" in updates:
            if updates["max_attendees"] is not None and updates["max_attendees"] <= 0:
                raise HTTPException(status_code=400, detail="max_attendees must be greater than 0")

    def _serialize_edit_request(self, edit_request: EventEditRequest) -> EventEditRequestResponse:
        return EventEditRequestResponse(
            id=edit_request.id,
            event_id=edit_request.event_id,
            status=edit_request.status,
            changes=edit_request.changes,
            requested_by=self._serialize_user(edit_request.requested_by),
            reviewer=self._serialize_user(edit_request.reviewer) if edit_request.reviewer else None,
            created_at=edit_request.created_at,
            reviewed_at=edit_request.reviewed_at,
            review_note=edit_request.review_note,
            event=self._serialize_event(edit_request.event),
        )

    async def create_event(self, data, user, images=None):
        try:
            # 0. Upload images if provided
            uploaded_urls = []
            if images:
                from app.common.services.s3_service import s3_service
                for file in images:
                    # Skip empty files
                    if file.size == 0 and not file.filename:
                        continue
                    url = s3_service.upload_file(file, folder="events")
                    uploaded_urls.append(url)
                
                if uploaded_urls:
                    data.image_urls = uploaded_urls

            # 1. Validate category exists
            category = await self._repository.get_category_by_id(data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            # 2. Create event model
            event = await self._repository.create_event(
                data=data,
                organizer_id=user.id
            )

            # 3. Add images
            if data.image_urls:
                await self._repository.add_event_images(event.id, data.image_urls)

            # 4. Reload event with relationships
            event = await self._repository.get_event_by_id(event.id)

            return event

        except Exception as e:
            # Rollback S3 uploads if DB transaction fails
            if images and 'uploaded_urls' in locals():
                from app.common.services.s3_service import s3_service
                for url in uploaded_urls:
                    s3_service.delete_file(url)
            raise e

    async def delete_event(self, event_id: str, user):
        # 1. Get event
        event = await self._repository.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # 2. Permission rules
        if not is_admin_or_owner(user, event.organizer_id):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "message": "Not authorized to delete this event"
                }
            )

        # 2.5 Cleanup S3 images
        from app.common.services.s3_service import s3_service
        if event.images:
            for image in event.images:
                 s3_service.delete_file(image.url)

        # 3. Delete event
        await self._repository.delete_event(event)

        # 4. Cleanup ChromaDB
        try:
            await chroma_service.delete_event_semantic(event.id)
            if event.category:
                await chroma_service.remove_event_from_category(event.category.name, event.id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"ChromaDB semantic delete failed for event {event.id}: {e}")

        return {"success": True, "message": "Event deleted successfully"}

    async def get_event(self, event_id: str) -> EventResponse:
        event = await self._repository.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return self._serialize_event(event)

    # Admin actions

    async def list_pending_events(self, query: EventListQuery) -> PaginatedEventsResponse:
        pending, total = await self._repository.list_pending_events(query)
        pagination = build_pagination_meta(query.page, query.page_size, total)
        return PaginatedEventsResponse(
            items=[self._serialize_event(event) for event in pending],
            pagination=pagination,
        )

    async def list_events_for_organizer(self, organizer_id: str, page: int, page_size: int) -> PaginatedEventsResponse:
        events, total = await self._repository.list_events_for_organizer(organizer_id, page, page_size)
        pagination = build_pagination_meta(page, page_size, total)
        return PaginatedEventsResponse(
            items=[self._serialize_event(event) for event in events],
            pagination=pagination,
        )

    async def get_recommended_events(self, user, limit: int = 10) -> PaginatedEventsResponse:
        interests = [interest.name for interest in getattr(user, "interests", [])]
        
        if not interests:
            # If user has no interests, return empty or default events list
            return PaginatedEventsResponse(items=[], pagination=build_pagination_meta(1, limit, 0))
            
        # Get recommended event IDs from ChromaDB
        event_ids = await chroma_service.get_recommended_event_ids(interests, limit)
        if not event_ids:
            return PaginatedEventsResponse(items=[], pagination=build_pagination_meta(1, limit, 0))
            
        # Fetch events by IDs from the repository
        events = await self._repository.get_events_by_ids(event_ids)
        
        # Re-order events to match the randomized event_ids order
        event_dict = {event.id: event for event in events}
        ordered_events = [event_dict[eid] for eid in event_ids if eid in event_dict]
        
        items = [self._serialize_event(event) for event in ordered_events]
        pagination = build_pagination_meta(1, limit, len(items))
        return PaginatedEventsResponse(items=items, pagination=pagination)

    async def request_event_edit(
        self,
        event_id: str,
        payload: EventEditRequestCreate,
        user,
    ) -> EventEditRequestResponse:
        event = await self._repository.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        if not is_admin_or_owner(user, event.organizer_id):
            raise HTTPException(status_code=403, detail="Not authorized to edit this event")

        pending_request = await self._repository.get_pending_edit_request_for_event(event_id)
        if pending_request:
            raise HTTPException(status_code=409, detail="Event already has a pending edit request")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No changes provided")

        if "category_id" in updates:
            category = await self._repository.get_category_by_id(updates["category_id"])
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

        self._validate_event_schedule(event, updates)

        changes = self._build_event_edit_changes(event, updates)
        if not changes:
            raise HTTPException(status_code=400, detail="No changes detected")

        edit_request = await self._repository.create_event_edit_request(event_id, user.id, changes)
        await self._repository.session.refresh(edit_request, ["event", "requested_by"])
        return self._serialize_edit_request(edit_request)

    async def list_event_edit_requests(
        self,
        status: Optional[str],
        page: int,
        page_size: int,
        search: Optional[str] = None,
        requested_by_id: Optional[str] = None,
    ) -> PaginatedEventEditRequestsResponse:
        if status and status not in {s.value for s in EventEditRequestStatus}:
            raise HTTPException(status_code=400, detail="Invalid status filter")

        requests, total = await self._repository.list_event_edit_requests(
            status,
            page,
            page_size,
            search,
            requested_by_id,
        )
        pagination = build_pagination_meta(page, page_size, total)
        return PaginatedEventEditRequestsResponse(
            items=[self._serialize_edit_request(item) for item in requests],
            pagination=pagination,
        )

    async def list_my_event_edit_requests(
        self,
        user_id: str,
        status: Optional[str],
        page: int,
        page_size: int,
        search: Optional[str] = None,
    ) -> PaginatedEventEditRequestsResponse:
        return await self.list_event_edit_requests(
            status=status,
            page=page,
            page_size=page_size,
            search=search,
            requested_by_id=user_id,
        )

    async def approve_event_edit_request(
        self,
        edit_request_id: str,
        user,
        review: Optional[EventEditRequestReview] = None,
    ) -> EventEditRequestResponse:
        if not is_admin(user):
            raise HTTPException(status_code=403, detail="Admin role required.")

        edit_request = await self._repository.get_event_edit_request_by_id(edit_request_id)
        if not edit_request:
            raise HTTPException(status_code=404, detail="Edit request not found")

        if edit_request.status != EventEditRequestStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Only pending edit requests can be approved")

        if not edit_request.event:
            raise HTTPException(status_code=404, detail="Event not found")

        self._assert_event_matches_changes(edit_request.event, edit_request.changes)

        updates = self._extract_updates_from_changes(edit_request.changes)
        self._validate_event_schedule(edit_request.event, updates)

        category_changed = "category_id" in updates and updates["category_id"] != edit_request.event.category_id
        old_category_name = None
        new_category_name = None
        
        if category_changed:
            old_category_name = edit_request.event.category.name if edit_request.event.category else None
            new_cat = await self._repository.get_category_by_id(updates["category_id"])
            if new_cat:
                new_category_name = new_cat.name

        for field, value in updates.items():
            setattr(edit_request.event, field, value)

        review_note = review.review_note if review else None
        await self._repository.update_event_edit_request_status(
            edit_request,
            EventEditRequestStatus.APPROVED.value,
            user.id,
            review_note,
        )
        await self._repository.session.refresh(edit_request, ["event", "requested_by", "reviewer"])
        
        # Sync event with ChromaDB
        try:
            if category_changed and old_category_name and new_category_name:
                await chroma_service.remove_event_from_category(old_category_name, edit_request.event.id)
                await chroma_service.upsert_event_category(new_category_name, edit_request.event.id)
            
            await chroma_service.upsert_event_semantic(edit_request.event.title, edit_request.event.description, edit_request.event.id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"ChromaDB update failed for event {edit_request.event.id}: {e}")
                
        return self._serialize_edit_request(edit_request)

    async def reject_event_edit_request(
        self,
        edit_request_id: str,
        user,
        review: Optional[EventEditRequestReview] = None,
    ) -> EventEditRequestResponse:
        if not is_admin(user):
            raise HTTPException(status_code=403, detail="Admin role required.")

        edit_request = await self._repository.get_event_edit_request_by_id(edit_request_id)
        if not edit_request:
            raise HTTPException(status_code=404, detail="Edit request not found")

        if edit_request.status != EventEditRequestStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Only pending edit requests can be rejected")

        review_note = review.review_note if review else None
        await self._repository.update_event_edit_request_status(
            edit_request,
            EventEditRequestStatus.REJECTED.value,
            user.id,
            review_note,
        )
        await self._repository.session.refresh(edit_request, ["event", "requested_by", "reviewer"])
        return self._serialize_edit_request(edit_request)

    async def approve_event(self, event_id: str, user):

        # 1. admin only
        if not is_admin(user):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "message": "Admin role required."}
            )

        # 2.GET event
        event = await self._repository.get_event_by_id_for_admin(event_id)
        if not event:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "Event not found."}
            )

        # 3. pending
        if event.status != EventStatus.PENDING.value:
            raise HTTPException(
                status_code=400,
                detail={"success": False, "message": "Only pending events can be approved."}
            )

        # 4. Update status
        updated_event = await self._repository.update_event_status(event_id, EventStatus.APPROVED.value)
        
        # 5. Create event group chat room and auto-add organizer and admins
        if updated_event:
            # Refresh event to ensure organizer relationship is loaded
            await self._repository.session.refresh(updated_event, ["organizer", "category"])
            await self._create_event_group_chat_room(updated_event, user)
            
            # Sync with ChromaDB upon approval
            try:
                await chroma_service.upsert_event_category(updated_event.category.name, updated_event.id)
                await chroma_service.upsert_event_semantic(updated_event.title, updated_event.description, updated_event.id)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"ChromaDB ingestion failed for event {updated_event.id}: {e}")
        
        return updated_event
    
    async def _create_event_group_chat_room(self, event: Event, admin_user):
        """Create event group chat room and auto-add organizer and all admins."""
        from app.chat.services.chat_service import ChatService
        from app.chat.models import ChatParticipantRole
        from app.auth.models import User, Role
        from app.auth.utils.auth_checks import is_admin
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        session = self._repository.session
        chat_service = ChatService(session)
        
        # Create or get the room
        room = await chat_service.ensure_event_group_room(event, admin_user)
        
        # Auto-add organizer
        if event.organizer_id:
            organizer = event.organizer if hasattr(event, 'organizer') and event.organizer else await session.get(User, event.organizer_id)
            if organizer:
                await chat_service.ensure_participant(room, organizer, ChatParticipantRole.OWNER)
        
        # Auto-add ALL admins
        admin_role_stmt = select(Role).where(Role.name == "admin")
        admin_role = (await session.scalars(admin_role_stmt)).first()
        if admin_role:
            # Get all users and check if they have admin role
            all_users_stmt = select(User).options(selectinload(User.roles))
            all_users = (await session.scalars(all_users_stmt)).all()
            for admin_user_obj in all_users:
                if is_admin(admin_user_obj):
                    await chat_service.ensure_participant(room, admin_user_obj, ChatParticipantRole.OWNER)
        
        await session.commit()

    async def reject_event(self, event_id: str, user):

        # 1. admin only
        if not is_admin(user):
            raise HTTPException(
                status_code=403,
                detail={"success": False, "message": "Admin role required."}
            )

        # 2. Get event
        event = await self._repository.get_event_by_id_for_admin(event_id)
        if not event:
            raise HTTPException(
                status_code=404,
                detail={"success": False, "message": "Event not found."}
            )

        # 3. pending
        if event.status != EventStatus.PENDING.value:
            raise HTTPException(
                status_code=400,
                detail={"success": False, "message": "Only pending events can be rejected."}
            )

        # 4. Update
        return await self._repository.update_event_status(event_id, EventStatus.REJECTED.value)
