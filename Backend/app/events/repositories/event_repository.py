from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.events.models import Event, EventCategory, EventEditRequest, EventEditRequestStatus
from app.events.schemas import EventListQuery


class EventRepository:
    """Persistence operations for events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_event_filters(self, base_conditions: list, query: EventListQuery) -> list:
        conditions = list(base_conditions)

        if query.category:
            conditions.append(
                Event.category.has(
                    func.lower(EventCategory.name) == query.category.lower()
                )
            )

        if query.search:
            like_value = f"%{query.search}%"
            search_conditions = [
                Event.title.ilike(like_value),
                Event.description.ilike(like_value),
            ]
            if getattr(query, "semantic_event_ids", None):
                search_conditions.append(Event.id.in_(query.semantic_event_ids))
                
            conditions.append(or_(*search_conditions))

        if query.location:
            conditions.append(Event.location.ilike(f"%{query.location}%"))

        if query.start_date_from:
            conditions.append(Event.start_date >= query.start_date_from)

        if query.start_date_to:
            conditions.append(Event.start_date <= query.start_date_to)

        if query.min_attendees is not None:
            conditions.append(Event.max_attendees >= query.min_attendees)

        if query.max_attendees is not None:
            conditions.append(Event.max_attendees <= query.max_attendees)

        if query.time_filter == "upcoming":
            conditions.append(
                or_(
                    Event.start_date > func.current_date(),
                    and_(
                        Event.start_date == func.current_date(),
                        Event.start_time > func.current_time(),
                    ),
                )
            )
        elif query.time_filter == "ongoing":
            conditions.append(
                and_(
                    or_(
                        Event.start_date < func.current_date(),
                        and_(
                            Event.start_date == func.current_date(),
                            Event.start_time <= func.current_time(),
                        ),
                    ),
                    or_(
                        Event.end_date > func.current_date(),
                        and_(
                            Event.end_date == func.current_date(),
                            Event.end_time >= func.current_time(),
                        ),
                    ),
                )
            )
        elif query.time_filter == "past":
            conditions.append(
                or_(
                    Event.end_date < func.current_date(),
                    and_(
                        Event.end_date == func.current_date(),
                        Event.end_time < func.current_time(),
                    ),
                )
            )

        return conditions

    def _resolve_sort_order(self, sort_by: str):
        sort_map = {
            "start_date_asc": [Event.start_date.asc(), Event.start_time.asc(), Event.title.asc()],
            "start_date_desc": [desc(Event.start_date), desc(Event.start_time), Event.title.asc()],
            "title_asc": [Event.title.asc(), Event.start_date.asc(), Event.start_time.asc()],
            "title_desc": [desc(Event.title), Event.start_date.asc(), Event.start_time.asc()],
            "max_attendees_desc": [desc(Event.max_attendees), Event.start_date.asc(), Event.start_time.asc()],
            "max_attendees_asc": [Event.max_attendees.asc(), Event.start_date.asc(), Event.start_time.asc()],
        }
        return sort_map.get(sort_by, sort_map["start_date_asc"])

    # get public events (approved only)
    async def list_public_events(self, query: EventListQuery) -> Tuple[List[Event], int]:
        conditions = self._apply_event_filters([Event.status == "approved"], query)
        order_by = self._resolve_sort_order(query.sort_by)

        stmt = (
            select(Event)
            .where(*conditions)
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
            .order_by(*order_by)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )

        events = (await self.session.scalars(stmt)).all()
        count_stmt = select(func.count(Event.id)).where(*conditions)
        total = await self.session.scalar(count_stmt)

        return events, int(total or 0)

    # get pending events
    async def list_pending_events(self, query: EventListQuery) -> Tuple[List[Event], int]:
        conditions = self._apply_event_filters([Event.status == "pending"], query)
        order_by = self._resolve_sort_order(query.sort_by)

        stmt = (
            select(Event)
            .where(*conditions)
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
            .order_by(*order_by)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )

        events = (await self.session.scalars(stmt)).all()
        count_stmt = select(func.count(Event.id)).where(*conditions)
        total = await self.session.scalar(count_stmt)  #

        return events, int(total or 0)

    async def list_events_for_organizer(self, organizer_id: str, page: int, page_size: int) -> Tuple[List[Event], int]:
        """Return paginated events created by the given organizer."""
        stmt = (
            select(Event)
            .where(Event.organizer_id == organizer_id)
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
            .order_by(Event.start_date.asc(), Event.start_time.asc(), Event.title.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        events = (await self.session.scalars(stmt)).all()
        count_stmt = select(func.count(Event.id)).where(Event.organizer_id == organizer_id)
        total = await self.session.scalar(count_stmt)

        return events, int(total or 0)

    # Categories
    async def get_category_by_id(self, category_id: str) -> Optional[EventCategory]:
        stmt = select(EventCategory).where(EventCategory.id == category_id)
        return await self.session.scalar(stmt)

    # Event creation
    async def create_event(self, data, organizer_id: str) -> Event:
        event = Event(
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            location=data.location,
            latitude=data.latitude,
            longitude=data.longitude,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
            sos_enabled=False,
            status="pending",
            max_attendees=data.max_attendees,
            organizer_id=organizer_id,
            category_id=data.category_id,
        )

        self.session.add(event)
        await self.session.flush()
        return event

    # Add images
    async def add_event_images(self, event_id: str, image_urls: List[str]):
        from app.events.models.event_image import EventImage

        for pos, url in enumerate(image_urls):
            img = EventImage(
                id=str(uuid.uuid4()),
                event_id=event_id,
                url=url,
                position=pos,
            )
            self.session.add(img)

        await self.session.flush()

    # GET events
    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
        )
        return await self.session.scalar(stmt)

    async def get_events_by_ids(self, event_ids: List[str]) -> List[Event]:
        if not event_ids:
            return []
        stmt = (
            select(Event)
            .where(Event.id.in_(event_ids))
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
        )
        return list((await self.session.scalars(stmt)).all())

    # DELETE event
    async def delete_event(self, event: Event):
        await self.session.delete(event)
        await self.session.flush()

    #Load event with relationship for admin
    async def get_event_by_id_for_admin(self, event_id: str) -> Optional[Event]:
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.category),
                selectinload(Event.organizer),
                selectinload(Event.images),
            )
        )
        return await self.session.scalar(stmt)

    #Update event status and return
    async def update_event_status(self, event_id: str, new_status: str) -> Optional[Event]:
        event = await self.get_event_by_id_for_admin(event_id)
        if not event:
            return None

        event.status = new_status
        await self.session.flush()
        return event

    # Event edit requests
    async def get_event_edit_request_by_id(self, edit_request_id: str) -> Optional[EventEditRequest]:
        stmt = (
            select(EventEditRequest)
            .where(EventEditRequest.id == edit_request_id)
            .options(
                selectinload(EventEditRequest.event).selectinload(Event.images),
                selectinload(EventEditRequest.event).selectinload(Event.category),
                selectinload(EventEditRequest.event).selectinload(Event.organizer),
                selectinload(EventEditRequest.requested_by),
                selectinload(EventEditRequest.reviewer),
            )
        )
        return await self.session.scalar(stmt)

    async def get_pending_edit_request_for_event(self, event_id: str) -> Optional[EventEditRequest]:
        stmt = (
            select(EventEditRequest)
            .where(
                EventEditRequest.event_id == event_id,
                EventEditRequest.status == EventEditRequestStatus.PENDING.value,
            )
            .order_by(EventEditRequest.created_at.desc())
        )
        return await self.session.scalar(stmt)

    async def list_event_edit_requests(
        self,
        status: Optional[str],
        page: int,
        page_size: int,
        search: Optional[str] = None,
        requested_by_id: Optional[str] = None,
    ) -> Tuple[List[EventEditRequest], int]:
        conditions = []
        if status:
            conditions.append(EventEditRequest.status == status)
        if requested_by_id:
            conditions.append(EventEditRequest.requested_by_id == requested_by_id)
        if search:
            like_value = f"%{search}%"
            conditions.append(Event.title.ilike(like_value))

        stmt = (
            select(EventEditRequest)
            .join(Event, Event.id == EventEditRequest.event_id)
            .where(*conditions)
            .options(
                selectinload(EventEditRequest.event).selectinload(Event.images),
                selectinload(EventEditRequest.event).selectinload(Event.category),
                selectinload(EventEditRequest.event).selectinload(Event.organizer),
                selectinload(EventEditRequest.requested_by),
                selectinload(EventEditRequest.reviewer),
            )
            .order_by(EventEditRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        requests = (await self.session.scalars(stmt)).all()

        count_stmt = (
            select(func.count(EventEditRequest.id))
            .select_from(EventEditRequest)
            .join(Event, Event.id == EventEditRequest.event_id)
            .where(*conditions)
        )
        total = await self.session.scalar(count_stmt)

        return requests, int(total or 0)

    async def create_event_edit_request(
        self,
        event_id: str,
        requested_by_id: str,
        changes: dict,
    ) -> EventEditRequest:
        edit_request = EventEditRequest(
            id=str(uuid.uuid4()),
            event_id=event_id,
            requested_by_id=requested_by_id,
            changes=changes,
            status=EventEditRequestStatus.PENDING.value,
        )
        self.session.add(edit_request)
        await self.session.flush()
        return edit_request

    async def update_event_edit_request_status(
        self,
        edit_request: EventEditRequest,
        new_status: str,
        reviewer_id: Optional[str],
        review_note: Optional[str] = None,
    ) -> EventEditRequest:
        edit_request.status = new_status
        edit_request.reviewer_id = reviewer_id
        edit_request.review_note = review_note
        from datetime import datetime
        edit_request.reviewed_at = datetime.utcnow()
        await self.session.flush()
        return edit_request
