from pydantic import BaseModel, Field
from typing import Optional, List


class UpdateUserDetailsSchema(BaseModel):
    first_names: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    profile_picture_url: Optional[str] = None
    interests: Optional[List[str]] = None

    # allow email field, but controller will block updating it
    email: Optional[str] = None

    class Config:
        extra = "allow"   # prevent 422 for extra fields

#change password
class ChangePasswordSchema(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    class Config:
        extra = "forbid"