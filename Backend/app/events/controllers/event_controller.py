from __future__ import annotations

from fastapi import Depends

from app.events.dependencies import get_event_service
from app.events.schemas import EventListQuery, PaginatedEventsResponse
from app.events.services import EventService


def get_event_controller(service: EventService = Depends(get_event_service)) -> "EventController":
    return EventController(service)


class EventController:
    """Coordinates request handling for events."""

    def __init__(self, service: EventService):
        self._service = service

    async def list_events(self, query: EventListQuery) -> PaginatedEventsResponse:
        return await self._service.list_public_events(query)

    async def list_recommended_events(self, user) -> PaginatedEventsResponse:
        return await self._service.get_recommended_events(user, limit=3)

    async def create_event(self, data, user, images=None):
        return await self._service.create_event(data, user, images)

    async def delete_event(self, event_id: str, user):
        return await self._service.delete_event(event_id, user)

    async def get_event(self, event_id: str):
        return await self._service.get_event(event_id)

    #  Admin Actions
    async def list_pending_events(self, query: EventListQuery):
        return await self._service.list_pending_events(query)

    async def approve_event(self, event_id: str, user):
        return await self._service.approve_event(event_id, user)

    async def reject_event(self, event_id: str, user):
        return await self._service.reject_event(event_id, user)

    async def list_organizer_events(self, organizer_id: str, page: int, page_size: int):
        return await self._service.list_events_for_organizer(organizer_id, page, page_size)

    async def request_event_edit(self, event_id: str, payload, user):
        return await self._service.request_event_edit(event_id, payload, user)

    async def list_event_edit_requests(
        self,
        status: str | None,
        page: int,
        page_size: int,
        search: str | None = None,
    ):
        return await self._service.list_event_edit_requests(status, page, page_size, search)

    async def list_my_event_edit_requests(
        self,
        user_id: str,
        status: str | None,
        page: int,
        page_size: int,
        search: str | None = None,
    ):
        return await self._service.list_my_event_edit_requests(user_id, status, page, page_size, search)

    async def approve_event_edit_request(self, edit_request_id: str, user, review=None):
        return await self._service.approve_event_edit_request(edit_request_id, user, review)

    async def reject_event_edit_request(self, edit_request_id: str, user, review=None):
        return await self._service.reject_event_edit_request(edit_request_id, user, review)
