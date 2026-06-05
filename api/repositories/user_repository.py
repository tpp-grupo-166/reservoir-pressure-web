"""SQLAlchemy-backed user repository implementation."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user import User
from domain.ports.user_repository_port import UserRepositoryPort
from infrastructure.db.models.user_model import UserModel


class UserRepository(UserRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- Port implementation -----

    async def save(self, user: User) -> User:
        """Persist a new user."""
        db_user = UserModel(id=user.id, email=user.email, password=user.password)
        self.db.add(db_user)
        return self._to_domain(db_user)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email. Returns None if not found."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        db_user = result.scalars().first()
        return self._to_domain(db_user) if db_user else None

    async def get_all(self) -> List[User]:
        """Return all users."""
        stmt = select(UserModel)
        result = await self.db.execute(stmt)
        users_model = result.scalars().all()
        return [self._to_domain(u) for u in users_model]

    # ----- Mapping helpers -----

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(id=model.id, email=model.email, password=model.password)
