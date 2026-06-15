from typing import List

from pydantic import BaseModel

from app.auth.presentation.user_response import UserResponse


class AdminListResponse(BaseModel):
    """Response schema for admin list."""
    
    admins: List[UserResponse]
