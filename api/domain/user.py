"""User domain model."""
from dataclasses import dataclass
from typing import Optional
import uuid

from core.security import verify_password


@dataclass
class User:
    """User entity with id, email, and password."""
    id: Optional[str] = None
    email: str = ""
    password: str = ""

    @classmethod
    def create(cls, email: str, hashed_password: str) -> "User":
        """Create a new User instance with generated UUID."""
        return cls(id=str(uuid.uuid4()), email=email, password=hashed_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify if the plain password matches the hashed password."""
        return verify_password(plain_password, self.password)
