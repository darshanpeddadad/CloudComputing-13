from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.admin.controllers import AdminController, get_admin_controller
from app.admin.presentation import AdminListResponse, PaginatedUsersResponse
from app.auth.dependencies import get_current_user, require_admin
from app.auth.models import User
from app.auth.presentation.user_response import UserResponse
from app.common import SuccessResponse, success_response


def get_admin_router() -> APIRouter:
    """Create and configure the admin router."""
    router = APIRouter(prefix="/api/admins", tags=["admins"])

    @router.get(
        "/",
        response_model=SuccessResponse[AdminListResponse],
        summary="Get list of all admin users",
        description="Returns a list of all users with admin role. Requires valid JWT token in Authorization header.",
    )
    async def get_admins(
        current_user: User = Depends(get_current_user),
        controller: AdminController = Depends(get_admin_controller),
    ):
        """
        Get list of all admin users.
        
        **Authentication Required**: This endpoint requires a valid JWT token in the Authorization header.
        Unauthenticated requests will receive a 401 Unauthorized response.
        """
        admin_data = await controller.get_all_admins()
        
        admin_responses = [
            UserResponse(
                id=admin["id"],
                first_names=admin["first_names"],
                last_name=admin["last_name"],
                email=admin["email"],
                dob=admin["dob"],
                roles=admin["roles"],
                interests=admin["interests"],
            )
            for admin in admin_data
        ]
        
        return success_response(AdminListResponse(admins=admin_responses))

    @router.get(
        "/users",
        response_model=SuccessResponse[PaginatedUsersResponse],
        summary="Get paginated list of all users",
        description="Returns a paginated list of all users. Only admins can access this endpoint.",
    )
    async def get_all_users(
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(10, ge=1, le=50, description="Number of items per page (max 50)"),
        search: Optional[str] = Query(None, description="Search term for filtering users by name or email"),
        admin_user: User = Depends(require_admin),
        controller: AdminController = Depends(get_admin_controller),
    ):
        """
        Get paginated list of all users.
        
        **Admin Only**: This endpoint requires admin role. Non-admin users will receive a 403 Forbidden response.
        Supports pagination and optional search filtering.
        """
        users_data, pagination = await controller.get_all_users_paginated(page, page_size, search)
        
        user_responses = [
            UserResponse(
                id=user["id"],
                first_names=user["first_names"],
                last_name=user["last_name"],
                email=user["email"],
                dob=user["dob"],
                roles=user["roles"],
                interests=user["interests"],
            )
            for user in users_data
        ]
        
        return success_response(
            PaginatedUsersResponse(items=user_responses, pagination=pagination)
        )

    return router
