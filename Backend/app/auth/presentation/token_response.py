from pydantic import BaseModel

from .user_response import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class Login2FARequiredResponse(BaseModel):
    message: str
    two_factor_required: bool = True
    temp_token: str
    
    model_config = {"populate_by_name": True}
