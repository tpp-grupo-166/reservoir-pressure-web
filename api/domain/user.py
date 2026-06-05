"""User domain model."""
from dataclasses import dataclass
from typing import Optional
import uuid
import re

from domain.errors import (
    InvalidEmailError,
    InvalidPasswordError,
)

MIN_PASSWORD_LENGTH = 8


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

    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format. Raises InvalidEmailError if invalid."""
        if not email or not isinstance(email, str):
            raise InvalidEmailError()
        
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            raise InvalidEmailError()

    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password requirements. Raises InvalidPasswordError if invalid."""
        if not password or not isinstance(password, str):
            raise InvalidPasswordError()
        
        if len(password) < MIN_PASSWORD_LENGTH:
            raise InvalidPasswordError()
        
        has_letter = re.search(r'[a-zA-Z]', password) is not None
        has_number = re.search(r'[0-9]', password) is not None
        
        if not (has_letter and has_number):
            raise InvalidPasswordError()
