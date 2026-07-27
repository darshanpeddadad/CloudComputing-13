from fastapi import Depends
from app.users.services.bookmark_service import BookmarkService
from app.users.repositories.bookmark_repository import BookmarkRepository
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_bookmark_controller(session: AsyncSession = Depends(get_session)) -> "BookmarkController":
    repository = BookmarkRepository(session)
    service = BookmarkService(repository)
    return BookmarkController(service)

class BookmarkController:
    def __init__(self, service: BookmarkService):
        self._service = service

    async def create_bookmark(self, user_id: str, event_id: str):
        return await self._service.create_bookmark(user_id, event_id)

    async def delete_bookmark(self, user_id: str, event_id: str):
        return await self._service.delete_bookmark(user_id, event_id)

    async def get_user_bookmarks(self, user_id: str):
        return await self._service.get_user_bookmarks(user_id)

    async def check_bookmark_status(self, user_id: str, event_id: str) -> bool:
        return await self._service.check_bookmark_status(user_id, event_id)
