from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.categories.repositories import CategoryRepository
from app.categories.services import CategoryService


def get_category_repository(session: AsyncSession = Depends(get_session)) -> CategoryRepository:
    return CategoryRepository(session)


def get_category_service(repository: CategoryRepository = Depends(get_category_repository)) -> CategoryService:
    return CategoryService(repository)
