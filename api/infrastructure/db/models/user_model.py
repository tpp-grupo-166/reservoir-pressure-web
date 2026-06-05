"""SQLAlchemy ORM model for the users table."""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from infrastructure.db.data_source import Base


class UserModel(Base):
    __tablename__ = "users"

    id         = Column(String, primary_key=True, index=True)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
