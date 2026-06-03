"""Pydantic schema for user registration."""
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """Schema for user registration."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
