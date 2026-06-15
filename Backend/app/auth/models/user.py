from typing import List, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.users.models.user_profile import UserProfile
from .associations import user_roles

if TYPE_CHECKING:
    from .role import Role
    from app.interests.models import Interest


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_names: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    dob: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 2FA fields
    two_factor_secret: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_two_factor_enabled: Mapped[bool] = mapped_column(default=False)
    backup_codes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        back_populates="users",
        secondary=user_roles,
        lazy="selectin",
    )
    interests: Mapped[List["Interest"]] = relationship(
        "Interest",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "first_names": self.first_names,
            "last_name": self.last_name,
            "email": self.email,
            "dob": self.dob,
            "roles": [role.name for role in self.roles],
            "interests": [interest.name for interest in self.interests],
        }
