from http import HTTPStatus
from typing import Dict, Optional
import pyotp
import qrcode
import io
import base64
import json

from ..exceptions import AuthError
from ..models import User
from ..repositories.interfaces import UserRepositoryProtocol
from ..schemas.auth import (
    Enable2FAResponse,
    Verify2FAResponse
)
from app.auth.security.jwt_service import create_access_token, decode_access_token

class TwoFactorService:
    """Service to handle Two-Factor Authentication logic."""

    def __init__(self, repository: UserRepositoryProtocol):
        self._repository = repository

    async def enable_2fa_request(self, user_id: str) -> Enable2FAResponse:
        user = await self._repository.get_by_id(user_id)
        if not user:
             raise AuthError("User not found.", HTTPStatus.NOT_FOUND)
        
        secret = pyotp.random_base32()
        
        user.two_factor_secret = secret
        await self._repository.update(user)
        
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="FuldaApp")
        
        img = qrcode.make(provisioning_uri)
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return Enable2FAResponse(secret=secret, qr_code=img_str)

    async def verify_2fa_enable(self, user_id: str, code: str) -> Verify2FAResponse:
        user = await self._repository.get_by_id(user_id)
        if not user or not user.two_factor_secret:
             raise AuthError("2FA setup not initiated.", HTTPStatus.BAD_REQUEST)

        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(code):
             raise AuthError("Invalid 2FA code.", HTTPStatus.UNAUTHORIZED)

        # Generate backup codes
        backup_codes = [pyotp.random_base32() for _ in range(10)]
        
        user.is_two_factor_enabled = True
        user.backup_codes = json.dumps(backup_codes)
        await self._repository.update(user)
        
        return Verify2FAResponse(backup_codes=backup_codes)

    async def verify_2fa_login(self, temp_token: str, code: str) -> Dict:
        try:
            payload = decode_access_token(temp_token)
            if payload.get("scope") != "2fa_pending":
                raise AuthError("Invalid token scope.", HTTPStatus.UNAUTHORIZED)
            user_id = payload.get("sub")
        except Exception:
            raise AuthError("Invalid or expired session.", HTTPStatus.UNAUTHORIZED)

        user = await self._repository.get_by_id(user_id)
        if not user:
            raise AuthError("User not found.", HTTPStatus.NOT_FOUND)

        # Check backup codes first
        is_backup_code = False
        if user.backup_codes:
            backup_codes = json.loads(user.backup_codes)
            if code in backup_codes:
                backup_codes.remove(code)
                user.backup_codes = json.dumps(backup_codes)
                await self._repository.update(user)
                is_backup_code = True
        
        if not is_backup_code:
            if not user.two_factor_secret:
                raise AuthError("2FA not enabled for user.", HTTPStatus.BAD_REQUEST)
            
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(code):
                 raise AuthError("Invalid 2FA code.", HTTPStatus.UNAUTHORIZED)

        token = create_access_token(
            user.id,
            claims={"email": user.email.lower()},
        )
        return {"access_token": token, "token_type": "bearer", "user": self._sanitize(user)}

    async def disable_2fa(self, user_id: str) -> None:
        user = await self._repository.get_by_id(user_id)
        if not user:
             raise AuthError("User not found.", HTTPStatus.NOT_FOUND)
        
        user.is_two_factor_enabled = False
        user.two_factor_secret = None
        user.backup_codes = None
        await self._repository.update(user)
        
    @staticmethod
    def _sanitize(user: Optional[User]) -> Dict:
        if not user:
            raise AuthError("User data unavailable.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return user.to_dict()
