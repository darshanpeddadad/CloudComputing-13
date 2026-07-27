from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.auth.models import User
from app.auth.security.auth_security import AuthSecurity
from app.auth.utils import is_admin, is_standard_user, user_from_token
from app.auth.repositories.user_repository import UserRepository
from app.auth.services.auth_service import AuthService
from app.interests.repositories import InterestRepository
from app.interests.services import InterestService

from app.auth.services.two_factor_service import TwoFactorService

def get_auth_security() -> AuthSecurity:
    return AuthSecurity()

async def get_two_factor_service(
    session: AsyncSession = Depends(get_session),
) -> TwoFactorService:
    user_repo = UserRepository(session)
    return TwoFactorService(user_repo)

async def get_auth_service(
    session: AsyncSession = Depends(get_session),
    security: AuthSecurity = Depends(get_auth_security),
) -> AuthService:
    user_repo = UserRepository(session)
    interest_repo = InterestRepository(session)
    interest_service = InterestService(interest_repo, security)
    return AuthService(user_repo, security, interest_service)


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve and return the current user from a bearer token."""
    try:
        user = await user_from_token(session, authorization)
    except JWTError:
        user = None
    if user:
        return user
    raise HTTPException(
        status_code=401,
        detail="Not authenticated."
    )


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has the admin role."""
    if not is_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return user


async def require_standard_user(user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has at least the standard user role."""
    if not is_standard_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role required.",
        )
    return user
