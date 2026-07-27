from pydantic import BaseModel, Field


class Enable2FAResponse(BaseModel):
    secret: str
    qr_code: str  # Base64 encoded image
    
class Verify2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")

class Verify2FAResponse(BaseModel):
    backup_codes: list[str]

class Login2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=32, description="TOTP code or backup code")
    temp_token: str
