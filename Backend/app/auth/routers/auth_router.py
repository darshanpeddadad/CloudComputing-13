from typing import List, Union

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.common import SuccessResponse, error_response, success_response
from ..controllers.auth_controller import AuthController, get_auth_controller
from ..exceptions import AuthError
from ..presentation import LoginRequest, RegistrationRequest, TokenResponse, UserResponse, Login2FARequiredResponse
from ..schemas.auth import (
    LoginCommand, 
    RegistrationCommand, 
    Enable2FAResponse,
    Verify2FARequest,
    Verify2FAResponse,
    Login2FARequest
)
from ..models import User
from ..dependencies import get_current_user


def get_auth_router() -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["authentication"])

    def _validation_detail(exc: ValidationError) -> List[dict]:
        formatted = []
        for error in exc.errors():
            msg = error.get("msg") or "Invalid input"
            formatted.append({"msg": msg})
        return formatted

    @router.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        response_model=SuccessResponse[UserResponse],
    )
    async def register(
        payload: RegistrationRequest,
        controller: AuthController = Depends(get_auth_controller),
    ):
        try:
            data = RegistrationCommand(**payload.model_dump())
        except ValidationError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response(
                    "Invalid input.",
                    code="validation_error",
                    details=_validation_detail(exc),
                ),
            )
        try:
            result = await controller.register(data)
            return success_response(result)
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )

    @router.post(
        "/login",
        response_model=SuccessResponse[Union[TokenResponse, Login2FARequiredResponse]],
    )
    async def login(
        payload: LoginRequest,
        controller: AuthController = Depends(get_auth_controller),
    ):
        try:
            data = LoginCommand(**payload.model_dump())
        except ValidationError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response(
                    "Invalid input.",
                    code="validation_error",
                    details=_validation_detail(exc),
                ),
            )
        try:
            result = await controller.login(data)
            return success_response(result)
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )


    @router.post("/2fa/enable", response_model=SuccessResponse[Enable2FAResponse])
    async def enable_2fa(
        controller: AuthController = Depends(get_auth_controller),
        user: User = Depends(get_current_user),
    ):
        try:
            result = await controller.enable_2fa_request(user.id)
            return success_response(result)
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )

    @router.post("/2fa/verify", response_model=SuccessResponse[Verify2FAResponse])
    async def verify_2fa(
        payload: Verify2FARequest,
        controller: AuthController = Depends(get_auth_controller),
        user: User = Depends(get_current_user),
    ):
        try:
            result = await controller.verify_2fa_enable(user.id, payload.code)
            return success_response(result)
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )

    @router.post("/2fa/login", response_model=SuccessResponse[TokenResponse])
    async def login_2fa(
        payload: Login2FARequest,
        controller: AuthController = Depends(get_auth_controller),
    ):
        try:
            result = await controller.verify_2fa_login(payload.temp_token, payload.code)
            return success_response(result)
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )

    @router.post("/2fa/disable")
    async def disable_2fa(
        controller: AuthController = Depends(get_auth_controller),
        user: User = Depends(get_current_user),
    ):
        try:
            await controller.disable_2fa(user.id)
            return success_response({"message": "2FA disabled successfully."})
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(exc.detail, code="auth_error"),
            )

    return router
