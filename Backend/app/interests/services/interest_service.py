from typing import Iterable, List

from app.interests.models.interest import Interest
from app.interests.repositories.interest_repository import InterestRepository
from app.auth.security.auth_security import AuthSecurity


class InterestService:
    def __init__(self, repository: InterestRepository, security: AuthSecurity):
        self._repository = repository
        self._security = security

    async def assign_interests(self, user_id: str, names: Iterable[str]) -> None:
        interests: List[Interest] = []
        for name in names:
            interests.append(
                Interest(
                    id=self._security.generate_interest_id(),
                    name=name,
                    user_id=user_id,
                )
            )
        await self._repository.replace_for_user(user_id, interests)
