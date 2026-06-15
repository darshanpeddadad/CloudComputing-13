import uuid

import bcrypt


class AuthSecurity:
    """Handles password hashing/verification and token/id generation."""

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def generate_token(self) -> str:
        return str(uuid.uuid4())

    def generate_user_id(self) -> str:
        return str(uuid.uuid4())

    def generate_interest_id(self) -> str:
        return str(uuid.uuid4())

    def generate_role_id(self) -> str:
        return str(uuid.uuid4())
