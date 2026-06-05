"""Domain facade. Orchestrates use cases using injected ports."""
import asyncio

from typing import List
from datetime import timedelta

from domain.user import User
from domain.ports.user_repository_port import UserRepositoryPort
from domain.errors import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from auth.security import Security


class System:
    def __init__(self, user_repository: UserRepositoryPort, security: Security,) -> None:
        self._user_repository = user_repository
        self._security = security

    # ── Users ───────────────────────────────────────────────────

    async def register_user(self, email: str, password: str) -> User:
        """Validate, hash password and persist a new user."""
        User.validate_email(email)
        User.validate_password(password)

        existing_user = await self._user_repository.find_by_email(email)
        if existing_user:
            raise EmailAlreadyExistsError()

        hashed_password = await asyncio.to_thread(self._security.hash_password, password)

        user = User.create(email, hashed_password)
        return await self._user_repository.save(user)

    async def get_all_users(self) -> List[User]:
        return await self._user_repository.get_all()

    # ── Auth ────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> str:
        """Validate credentials and return a signed JWT. Raises InvalidCredentialsError on failure."""
        User.validate_email(email)
        user = await self._user_repository.find_by_email(email)

        if not user or not await asyncio.to_thread(self._security.verify_password, password, user.password):
            raise InvalidCredentialsError()

        return self._security.create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=self._security.expire_minutes),
        )

    async def get_user_from_token(self, token: str) -> User:
        """Decode JWT and return the corresponding User. Raises UserNotFoundError if invalid."""
        payload = self._security.decode_access_token(token)
        if not payload or "sub" not in payload:
            raise UserNotFoundError()
    
        email = payload["sub"]
        user = await self._user_repository.find_by_email(email)
        if not user:
            raise UserNotFoundError()

        return user
