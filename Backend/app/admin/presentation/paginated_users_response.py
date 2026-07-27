from typing import List

from pydantic import BaseModel

from app.auth.presentation.user_response import UserResponse
from app.common.pagination import PaginationMeta


class PaginatedUsersResponse(BaseModel):
    """Response schema for paginated users list."""
    
    items: List[UserResponse]
    pagination: PaginationMeta
