from datetime import timedelta
from http import HTTPStatus
from typing import Dict, Optional

from ..exceptions import AuthError
from ..models import User
from ..repositories.interfaces import UserRepositoryProtocol
from ..schemas.auth import LoginCommand, RegistrationCommand
from ..security.auth_security import AuthSecurity
from app.auth.security.jwt_service import create_access_token
from app.interests.services import InterestService
from ..schemas.auth import (
    LoginCommand, 
    RegistrationCommand
)


class AuthService:
    """Core authentication business logic."""

    def __init__(
        self,
        repository: UserRepositoryProtocol,
        security: AuthSecurity,
        interest_service: InterestService,
    ):
        self._repository = repository
        self._security = security
        self._interest_service = interest_service

    async def register(self, data: RegistrationCommand) -> Dict:
        normalized_email = data.email.lower()
        existing = await self._repository.get_by_email(normalized_email)
        if existing:
            raise AuthError("User already exists.", HTTPStatus.CONFLICT)

        user = User(
            id=self._security.generate_user_id(),
            first_names=data.first_names,
            last_name=data.last_name,
            email=normalized_email,
            dob=data.dob,
            password_hash=self._security.hash_password(data.password),
            roles=[],
        )
        persisted = await self._repository.create_user_with_role(user)
        await self._interest_service.assign_interests(persisted.id, data.interests)
        reloaded = await self._repository.get_by_email(persisted.email)
        sanitized = self._sanitize(reloaded)
        sanitized["interests"] = data.interests
        return sanitized

    async def login(self, data: LoginCommand) -> Dict:
        user = await self._repository.get_by_email(data.email.lower())
        if not user or not self._security.verify_password(data.password, user.password_hash):
            raise AuthError("Invalid credentials.", HTTPStatus.UNAUTHORIZED)

        if user.is_two_factor_enabled:
            temp_token = create_access_token(
                user.id,
                claims={"email": user.email.lower(), "scope": "2fa_pending", "type": "temp_login"},
                expires_delta=timedelta(minutes=5)
            )
            return {
                "message": "2FA required",
                "2fa_required": True,
                "temp_token": temp_token
            }

        token = create_access_token(
            user.id,
            claims={"email": user.email.lower()},
        )
        return {"access_token": token, "token_type": "bearer", "user": self._sanitize(user)}

    @staticmethod
    def _sanitize(user: Optional[User]) -> Dict:
        if not user:
            raise AuthError("User data unavailable.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return user.to_dict()
