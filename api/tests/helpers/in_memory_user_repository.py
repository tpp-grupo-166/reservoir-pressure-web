from typing import Dict, List, Optional
import uuid

from domain.user import User
from domain.ports.user_repository_port import UserRepositoryPort

class InMemoryUserRepository(UserRepositoryPort):
    """In-memory implementation of UserRepositoryPort for testing."""

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}

    async def save(self, user: User) -> User:
        self._users[user.email] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        return self._users.get(email)

    async def get_all(self) -> List[User]:
        return list(self._users.values())
