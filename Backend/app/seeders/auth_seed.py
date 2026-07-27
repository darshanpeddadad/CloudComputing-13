import os
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import Role, User
from app.auth.security.auth_security import AuthSecurity

ROLE_NAMES: Sequence[str] = ("admin", "user")


async def seed_roles_and_admin(session: AsyncSession, security: AuthSecurity) -> None:
    created_role = False
    for role_name in ROLE_NAMES:
        existing = await session.scalar(select(Role).where(Role.name == role_name))
        if not existing:
            session.add(Role(id=security.generate_role_id(), name=role_name))
            created_role = True
    if created_role:
        await session.flush()

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password:
        admin_email = admin_email.lower()
        admin_stmt = select(User).where(User.email == admin_email).options(selectinload(User.roles))
        admin_user = await session.scalar(admin_stmt)
        if not admin_user:
            admin_user = User(
                id=security.generate_user_id(),
                first_names=os.getenv("ADMIN_FIRST_NAMES", "Fulda"),
                last_name=os.getenv("ADMIN_LAST_NAME", "Admin"),
                email=admin_email,
                dob=os.getenv("ADMIN_DOB", "1990-01-01"),
                password_hash=security.hash_password(admin_password),
            )
            admin_role = await session.scalar(select(Role).where(Role.name == "admin"))
            if admin_role:
                admin_user.roles = [admin_role]
            session.add(admin_user)
        else:
            admin_role = await session.scalar(select(Role).where(Role.name == "admin"))
            if admin_role and admin_role not in admin_user.roles:
                admin_user.roles.append(admin_role)
        await session.commit()
    else:
        await session.commit()
