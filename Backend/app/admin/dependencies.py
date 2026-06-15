from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories.user_repository import UserRepository
from app.database import get_session
from app.admin.services.admin_service import AdminService


async def get_admin_service(session: AsyncSession = Depends(get_session)) -> AdminService:
    """Dependency to get AdminService instance."""
    user_repository = UserRepository(session)
    return AdminService(user_repository)
