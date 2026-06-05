"""SQL-backed user repository using SQLAlchemy."""
from typing import Optional, List
from sqlalchemy.orm import Session

from domain.user import User
from domain.ports.user_repository_port import UserRepositoryPort
from infrastructure.db.models.user_model import UserModel


def _to_domain(model: UserModel) -> User:
    """Convert ORM model to domain entity."""
    return User(id=model.id, email=model.email, password=model.password)


class UserRepository(UserRepositoryPort):
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> User:
        """Persist a new user."""
        db_user = UserModel(id=user.id, email=user.email, password=user.password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return _to_domain(db_user)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email. Returns None if not found."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return _to_domain(db_user) if db_user else None

    def get_all(self) -> List[User]:
        """Return all users."""
        return [_to_domain(u) for u in self.db.query(UserModel).all()]
