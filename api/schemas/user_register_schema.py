"""Pydantic schema for user registration."""
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
