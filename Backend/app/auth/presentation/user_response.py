from typing import List

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    first_names: str
    last_name: str
    email: EmailStr
    dob: str
    roles: List[str]
    interests: List[str]
