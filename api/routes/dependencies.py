"""FastAPI dependency that wires the System with its concrete implementations."""
from fastapi import Depends
from sqlalchemy.orm import Session

from auth.security import Security
from domain.system import System
from repositories.user_repository import UserRepository
from infrastructure.db.data_source import get_db


def get_security() -> Security:
    return Security()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_system(
    user_repository: UserRepository = Depends(get_user_repository),
    security: Security = Depends(get_security),
) -> System:
    return System(user_repository=user_repository, security=security)
