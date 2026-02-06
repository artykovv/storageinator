from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.role import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """User document in database."""
    id: str = Field(..., alias="_id")
    email: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    
    class Config:
        populate_by_name = True


class UserResponse(BaseModel):
    """User response schema (public data)."""
    id: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user (admin only)."""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=100)
