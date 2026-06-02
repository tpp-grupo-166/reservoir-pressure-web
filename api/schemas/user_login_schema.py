"""Pydantic schema for user login."""
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
