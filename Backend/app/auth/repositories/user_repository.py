import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Role, User


class UserRepository:
    """SQLAlchemy-powered persistence layer for users."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.roles), selectinload(User.interests))
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles), selectinload(User.interests))
        )
        result = await self._session.scalars(stmt)
        return result.first()

    async def update(self, user: User) -> None:
        self._session.add(user)
        await self._session.flush()

    async def get_all_admins(self) -> List[User]:
        """Get all users with the admin role."""
        from ..models.associations import user_roles
        
        admin_role_stmt = select(Role).where(Role.name == "admin")
        admin_role = await self._session.scalar(admin_role_stmt)
        
        if not admin_role:
            return []
        
        stmt = (
            select(User)
            .join(user_roles, User.id == user_roles.c.user_id)
            .where(user_roles.c.role_id == admin_role.id)
            .options(selectinload(User.roles), selectinload(User.interests))
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_all_users(
        self, page: int, page_size: int, search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """Get all users with pagination and optional search."""
        conditions = []
        
        if search:
            search_term = f"%{search}%"
            conditions.extend([
                User.first_names.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
            ])
        
        base_stmt = select(User)
        if conditions:
            base_stmt = base_stmt.where(or_(*conditions))
        
        stmt = (
            base_stmt
            .options(selectinload(User.roles), selectinload(User.interests))
            .order_by(User.email.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        users = (await self._session.scalars(stmt)).all()
        
        count_stmt = select(func.count(User.id))
        if conditions:
            count_stmt = count_stmt.where(or_(*conditions))
        total = await self._session.scalar(count_stmt)
        
        return list(users), int(total or 0)

    async def create_user_with_role(self, user: User, role_name: str = "user") -> User:
        user.email = user.email.lower()
        role = await self._get_or_create_role(role_name)
        user.roles = [role]
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def _get_or_create_role(self, role_name: str) -> Role:
        stmt = select(Role).where(Role.name == role_name)
        result = await self._session.scalars(stmt)
        role = result.first()
        if role:
            return role
        role = Role(id=self._role_id(role_name), name=role_name)
        self._session.add(role)
        await self._session.flush()
        return role

    @staticmethod
    def _role_id(name: str) -> str:
        return f"role-{name}-{uuid.uuid4().hex[:6]}"
