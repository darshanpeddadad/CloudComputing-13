import re
from typing import List

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

_FULDA_PATTERN = re.compile(r"^[^@\s]+@([a-z0-9-]+\.)*hs-fulda\.de$", re.IGNORECASE)


class RegistrationCommand(BaseModel):
    first_names: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    dob: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    interests: List[str]

    @field_validator("email", mode="before")
    @classmethod
    def enforce_hs_fulda_domain(cls, value: str) -> str:
        lowered = value.lower()
        if not _FULDA_PATTERN.match(lowered):
            raise ValueError("Email must belong to hs-fulda.de domain")
        return lowered

    @field_validator("interests", mode="after")
    @classmethod
    def validate_interests(cls, value: List[str]) -> List[str]:
        filtered = [interest.strip() for interest in value if interest.strip()]
        if not filtered:
            raise ValueError("At least one interest must be provided.")
        return filtered

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords must match")
        return self
