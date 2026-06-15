from __future__ import annotations

from typing import List

from fastapi import Depends

from app.categories.dependencies import get_category_service
from app.categories.schemas import CategoryResponse
from app.categories.services import CategoryService


def get_category_controller(service: CategoryService = Depends(get_category_service)) -> "CategoryController":
    return CategoryController(service)


class CategoryController:
    """Coordinates request handling for categories."""

    def __init__(self, service: CategoryService):
        self._service = service

    async def list_categories(self) -> List[CategoryResponse]:
        return await self._service.list_categories()
