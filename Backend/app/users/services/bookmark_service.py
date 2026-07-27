from fastapi import HTTPException
from typing import List

from app.users.repositories.bookmark_repository import BookmarkRepository
from app.users.schemas.bookmark_schema import BookmarkResponse, BookmarkStatus
from app.events.schemas.event_response import EventResponse
from app.events.schemas.event_category_schema import EventCategorySchema
from app.events.schemas.event_organizer_schema import EventOrganizerSchema
from app.events.models.event import Event

class BookmarkService:
    def __init__(self, repository: BookmarkRepository):
        self._repository = repository

    async def create_bookmark(self, user_id: str, event_id: str) -> None:
        # Check if already bookmarked
        existing = await self._repository.get_by_user_and_event(user_id, event_id)
        if existing:
            raise HTTPException(status_code=409, detail="Bookmark already exists") 
        try:
            await self._repository.create(user_id, event_id)
        except Exception as e:
            pass

    async def delete_bookmark(self, user_id: str, event_id: str) -> None:
        deleted = await self._repository.delete(user_id, event_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Bookmark not found")

    async def get_user_bookmarks(self, user_id: str) -> List[BookmarkResponse]:
        bookmarks = await self._repository.get_all_by_user(user_id)
        
        response = []
        for bookmark in bookmarks:
            event = bookmark.event
            organizer_name = f"{event.organizer.first_names} {event.organizer.last_name}".strip()
            image_urls = [image.url for image in sorted(event.images, key=lambda img: (img.position, img.id))]
            
            event_response = EventResponse(
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
            
            response.append(BookmarkResponse(
                user_id=bookmark.user_id,
                event_id=bookmark.event_id,
                event=event_response
            ))
            
        return response

    async def check_bookmark_status(self, user_id: str, event_id: str) -> bool:
        bookmark = await self._repository.get_by_user_and_event(user_id, event_id)
        return bookmark is not None
