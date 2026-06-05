"""Abstract port for user persistence. Part of the domain layer."""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.user import User


class UserRepositoryPort(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a new user. Raises EmailAlreadyExistsError if email is taken."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Return the user with the given email, or None if not found."""
        ...

    @abstractmethod
    async def get_all(self) -> List[User]:
        """Return all persisted users."""
        ...
