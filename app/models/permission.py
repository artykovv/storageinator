from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class PermissionType(str, Enum):
    """Types of permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class PermissionGrant(BaseModel):
    """Schema for granting permissions."""
    user_email: str  # Grant by email for easier UX
    permissions: List[PermissionType]


class PermissionInDB(BaseModel):
    """Permission document in database."""
    id: str = Field(..., alias="_id")
    user_id: str
    directory_id: str
    permissions: List[PermissionType]
    granted_by: str
    created_at: datetime

    class Config:
        populate_by_name = True


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: str
    user_id: str
    user_email: str
    directory_id: str
    permissions: List[PermissionType]
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionListResponse(BaseModel):
    """List of permissions for a directory."""
    permissions: List[PermissionResponse]
    directory_id: str
