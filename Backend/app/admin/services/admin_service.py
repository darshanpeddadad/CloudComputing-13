from typing import List, Optional, Tuple

from app.auth.repositories.interfaces import UserRepositoryProtocol
from app.auth.models import User
from app.common.pagination import PaginationMeta, build_pagination_meta


class AdminService:
    """Business logic for admin operations."""

    def __init__(self, user_repository: UserRepositoryProtocol):
        self._user_repository = user_repository

    async def get_all_admins(self) -> List[dict]:
        """Get all users with the admin role."""
        admin_users = await self._user_repository.get_all_admins()
        return [self._sanitize_user(user) for user in admin_users]

    async def get_all_users_paginated(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> Tuple[List[dict], PaginationMeta]:
        """Get all users with pagination and optional search."""
        users, total = await self._user_repository.list_all_users(page, page_size, search)
        pagination = build_pagination_meta(page, page_size, total)
        return [self._sanitize_user(user) for user in users], pagination

    @staticmethod
    def _sanitize_user(user: User) -> dict:
        """Convert User model to dictionary representation."""
        return user.to_dict()
