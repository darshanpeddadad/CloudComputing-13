from typing import List, Optional, Protocol, Tuple

from app.auth.models import User


class UserRepositoryProtocol(Protocol):
    async def get_by_email(self, email: str) -> Optional[User]:
        ...

    async def create_user_with_role(self, user: User, role_name: str = "user") -> User:
        ...

    async def get_all_admins(self) -> List[User]:
        ...

    async def list_all_users(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        ...

    async def get_by_id(self, user_id: str) -> Optional[User]:
        ...

    async def update(self, user: User) -> None:
        ...
