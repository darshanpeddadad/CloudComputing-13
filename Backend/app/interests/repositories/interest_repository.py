from typing import Iterable

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.interests.models.interest import Interest


class InterestRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def replace_for_user(self, user_id: str, interests: Iterable[Interest]) -> None:
        await self._session.execute(delete(Interest).where(Interest.user_id == user_id))
        for interest in interests:
            self._session.add(interest)
        await self._session.flush()
