from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.categories.controllers import CategoryController, get_category_controller
from app.categories.schemas import CategoryResponse
from app.common import SuccessResponse, success_response


def get_category_router() -> APIRouter:
    router = APIRouter(prefix="/api/categories", tags=["categories"])

    @router.get("/", response_model=SuccessResponse[List[CategoryResponse]])
    async def list_categories(
        controller: CategoryController = Depends(get_category_controller),
        current_user: User = Depends(get_current_user),
    ):
        """List all event categories. Requires authentication."""
        categories = await controller.list_categories()
        return success_response(categories, message="Categories fetched successfully")

    return router
