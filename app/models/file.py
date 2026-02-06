from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FileUploadRequest(BaseModel):
    """Schema for requesting a presigned upload URL."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    size: int = Field(..., gt=0)
    directory_id: str


class FileUploadResponse(BaseModel):
    """Response with presigned upload URL."""
    presigned_url: str
    file_id: str
    expires_in: int = 3600


class FileConfirm(BaseModel):
    """Schema for confirming file upload."""
    sha256: str = Field(..., min_length=64, max_length=64)


class FileInDB(BaseModel):
    """File document in database."""
    id: str = Field(..., alias="_id")
    filename: str
    s3_key: str
    content_type: str
    size: int
    sha256: Optional[str] = None
    directory_id: str
    owner_id: str
    created_at: datetime
    confirmed: bool = False
    is_public: bool = False

    class Config:
        populate_by_name = True


class FileResponse(BaseModel):
    """File response schema."""
    id: str
    filename: str
    content_type: str
    size: int
    directory_id: str
    created_at: datetime
    is_public: bool = False

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    """Schema for updating file."""
    is_public: Optional[bool] = None


class FileDownloadResponse(BaseModel):
    """Response with presigned download URL."""
    presigned_url: str
    filename: str
    expires_in: int = 3600


class FileListResponse(BaseModel):
    """List of files response."""
    files: List[FileResponse]
    total: int
