from fastapi import Depends

from ..dependencies import get_auth_service, get_two_factor_service
from ..schemas.auth import LoginCommand, RegistrationCommand
from ..services.auth_service import AuthService
from ..services.two_factor_service import TwoFactorService


def get_auth_controller(
    service: AuthService = Depends(get_auth_service),
    two_factor_service: TwoFactorService = Depends(get_two_factor_service)
) -> "AuthController":
    return AuthController(service, two_factor_service)


class AuthController:
    """Coordinates presentation inputs to service operations."""

    def __init__(self, service: AuthService, two_factor_service: TwoFactorService):
        self._service = service
        self._two_factor_service = two_factor_service

    async def register(self, data: RegistrationCommand):
        return await self._service.register(data)

    async def login(self, data: LoginCommand):
        return await self._service.login(data)

    async def enable_2fa_request(self, user_id: str):
        return await self._two_factor_service.enable_2fa_request(user_id)

    async def verify_2fa_enable(self, user_id: str, code: str):
        return await self._two_factor_service.verify_2fa_enable(user_id, code)

    async def verify_2fa_login(self, temp_token: str, code: str):
        return await self._two_factor_service.verify_2fa_login(temp_token, code)

    async def disable_2fa(self, user_id: str):
        return await self._two_factor_service.disable_2fa(user_id)
