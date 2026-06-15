from typing import Optional

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.security.jwt_service import decode_access_token


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """Return bearer token from Authorization header, if present."""
    if not authorization_header:
        return None
    scheme, _, token = authorization_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip() or None


def is_logged_in(authorization_header: Optional[str]) -> bool:
    """Lightweight check to see if a bearer token is present and valid."""
    token = extract_bearer_token(authorization_header)
    if not token:
        return False
    try:
        decode_access_token(token)
        return True
    except JWTError:
        return False


async def user_from_token(
    session: AsyncSession,
    authorization_header: Optional[str],
) -> Optional[User]:
    """Resolve a user instance from an Authorization header, if possible."""
    token = extract_bearer_token(authorization_header)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return await session.get(User, user_id)


def has_role(user: User, role_name: str) -> bool:
    """Check if a user has a role by name (case-insensitive)."""
    return any(role.name.lower() == role_name.lower() for role in user.roles)


def is_admin(user: User) -> bool:
    return has_role(user, "admin")


def is_standard_user(user: User) -> bool:
    return has_role(user, "user")


def is_admin_or_owner(user: User, owner_id: Optional[str]) -> bool:
    if not owner_id:
        return False
    return is_admin(user) or user.id == owner_id
