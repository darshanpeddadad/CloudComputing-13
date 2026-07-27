from typing import List

from pydantic import BaseModel, EmailStr, Field


class RegistrationRequest(BaseModel):
    first_names: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    dob: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    interests: List[str]
