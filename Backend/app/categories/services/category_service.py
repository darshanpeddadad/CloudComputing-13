from __future__ import annotations

from typing import List

from app.categories.repositories import CategoryRepository
from app.categories.schemas import CategoryResponse


class CategoryService:
    """Business logic for querying categories."""

    def __init__(self, repository: CategoryRepository):
        self._repository = repository

    async def list_categories(self) -> List[CategoryResponse]:
        """List all event categories."""
        categories = await self._repository.list_all_categories()
        return [CategoryResponse(id=cat.id, name=cat.name) for cat in categories]
