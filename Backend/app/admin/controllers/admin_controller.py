from typing import List, Optional, Tuple

from fastapi import Depends

from app.admin.dependencies import get_admin_service
from app.admin.services.admin_service import AdminService
from app.common.pagination import PaginationMeta


def get_admin_controller(service: AdminService = Depends(get_admin_service)) -> "AdminController":
    """Dependency to get AdminController instance."""
    return AdminController(service)


class AdminController:
    """Coordinates presentation inputs to admin service operations."""

    def __init__(self, service: AdminService):
        self._service = service

    async def get_all_admins(self):
        """Get all admin users."""
        return await self._service.get_all_admins()

    async def get_all_users_paginated(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> Tuple[List[dict], PaginationMeta]:
        """Get all users with pagination."""
        return await self._service.get_all_users_paginated(page, page_size, search)
