"""Pydantic schema for JWT token response."""
from pydantic import BaseModel


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
