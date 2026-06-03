"""In-memory user store and authentication service."""
from typing import List, Optional

from domain.user import User
from domain.errors import EmailAlreadyExistsError


# In-memory user store
users: List[User] = []


class UserService:
    """Service for managing users in memory."""

    @staticmethod
    def save(user: User) -> User:
        """Save a user instance to the in-memory store."""
        if UserService.find_by_email(user.email):
            raise EmailAlreadyExistsError()
        users.append(user)
        return user

    @staticmethod
    def find_by_email(email: str) -> Optional[User]:
        """Get a user by email."""
        return next((u for u in users if u.email == email), None)

    @staticmethod
    def get_all() -> List[User]:
        """Get all users."""
        return users
