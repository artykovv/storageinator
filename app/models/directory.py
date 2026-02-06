from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DirectoryCreate(BaseModel):
    """Schema for creating a directory."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[str] = None
    is_public: bool = False  # Public directories accessible to all users


class DirectoryUpdate(BaseModel):
    """Schema for updating a directory."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_public: Optional[bool] = None


class DirectoryInDB(BaseModel):
    """Directory document in database."""
    id: str = Field(..., alias="_id")
    name: str
    owner_id: str
    parent_id: Optional[str] = None
    path: str  # Full path like /root/folder1/folder2
    is_public: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True


class DirectoryResponse(BaseModel):
    """Directory response schema."""
    id: str
    name: str
    path: str
    parent_id: Optional[str] = None
    is_public: bool = False
    owner_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DirectoryTree(BaseModel):
    """Directory with nested children."""
    id: str
    name: str
    path: str
    parent_id: Optional[str] = None
    is_public: bool = False
    owner_id: str
    created_at: datetime
    children: List["DirectoryTree"] = []
    
    class Config:
        from_attributes = True


# Enable forward reference
DirectoryTree.model_rebuild()
