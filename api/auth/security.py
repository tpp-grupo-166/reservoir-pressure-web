"""Security service: password hashing and JWT management."""
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv()


class Security:
    def __init__(
        self,
        secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production"),
        algorithm: str = os.getenv("ALGORITHM", "HS256"),
        expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # ── Password ────────────────────────────────────────────────

    def hash_password(self, plain_password: str) -> str:
        """Return bcrypt hash of plain_password."""
        return self._pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True if plain_password matches hashed_password."""
        return self._pwd_context.verify(plain_password, hashed_password)

    # ── JWT ─────────────────────────────────────────────────────

    def create_access_token(
        self, data: dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Encode and sign a JWT with an expiry claim."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self._expire_minutes))
        to_encode["exp"] = expire
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Decode and verify a JWT. Returns {} on any error."""
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError:
            return {}

    @property
    def expire_minutes(self) -> int:
        return self._expire_minutes
