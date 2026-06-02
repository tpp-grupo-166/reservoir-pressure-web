"""Pydantic schema for user response."""
from pydantic import BaseModel


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str