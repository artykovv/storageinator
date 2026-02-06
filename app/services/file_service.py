from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
import uuid

from app.db.mongodb import get_files_collection, get_directories_collection
from app.db.s3 import get_s3_client
from app.core.config import settings
from app.models.file import (
    FileUploadRequest,
    FileUploadResponse,
    FileResponse,
    FileDownloadResponse,
    FileUpdate,
)
from app.models.role import UserRole


class FileService:
    """Service for file operations."""

    @staticmethod
    async def update_file(
        file_id: str,
        update_data: FileUpdate,
        user_id: str,
    ) -> Optional[FileResponse]:
        """Update file status."""
        files = get_files_collection()
        
        file_doc = await files.find_one({"_id": file_id})
        if not file_doc:
            return None
            
        update_doc = {}
        if update_data.is_public is not None:
            update_doc["is_public"] = update_data.is_public
            
        if not update_doc:
            return FileResponse(**file_doc)
            
        await files.update_one(
            {"_id": file_id},
            {"$set": update_doc}
        )
        
        updated_doc = await files.find_one({"_id": file_id})
        return FileResponse(
            id=updated_doc["_id"],
            filename=updated_doc["filename"],
            content_type=updated_doc["content_type"],
            size=updated_doc["size"],
            directory_id=updated_doc["directory_id"],
            created_at=updated_doc["created_at"],
            is_public=updated_doc.get("is_public", False),
        )

    @staticmethod
    async def get_public_file(file_id: str) -> Optional[dict]:
        """Get public file document."""
        files = get_files_collection()
        print(f"DEBUG: Finding public file {file_id}")
        return await files.find_one({"_id": file_id, "confirmed": True, "is_public": True})

    @staticmethod
    def _validate_mime_type(content_type: str) -> bool:
        """Validate if MIME type is allowed."""
        return content_type in settings.allowed_mime_types_list

    @staticmethod
    def _validate_file_size(size: int) -> bool:
        """Validate if file size is within limits."""
        return size <= settings.max_file_size_bytes

    @staticmethod
    async def request_upload(
        data: FileUploadRequest,
        user_id: str,
    ) -> FileUploadResponse:
        """Request a presigned URL for file upload."""
        # Validate MIME type
        if not FileService._validate_mime_type(data.content_type):
            raise ValueError(f"MIME type not allowed: {data.content_type}")
        
        # Validate file size
        if not FileService._validate_file_size(data.size):
            max_mb = settings.max_file_size_mb
            raise ValueError(f"File size exceeds limit of {max_mb}MB")
        
        # Check directory exists
        directories = get_directories_collection()
        directory = await directories.find_one({"_id": data.directory_id})
        if not directory:
            raise ValueError("Directory not found")
        
        # Generate S3 key
        file_id = str(ObjectId())
        unique_prefix = str(uuid.uuid4())[:8]
        s3_key = f"{data.directory_id}/{unique_prefix}_{data.filename}"
        
        # Create file record (unconfirmed)
        files = get_files_collection()
        file_doc = {
            "_id": file_id,
            "filename": data.filename,
            "s3_key": s3_key,
            "content_type": data.content_type,
            "size": data.size,
            "sha256": None,
            "directory_id": data.directory_id,
            "owner_id": user_id,
            "created_at": datetime.now(timezone.utc),
            "confirmed": False,
        }
        await files.insert_one(file_doc)
        
        # Generate presigned URL
        s3_client = get_s3_client()
        presigned_url = s3_client.generate_presigned_put_url(
            key=s3_key,
            content_type=data.content_type,
            expires_in=3600,
        )
        
        return FileUploadResponse(
            presigned_url=presigned_url,
            file_id=file_id,
            expires_in=3600,
        )

    @staticmethod
    async def confirm_upload(
        file_id: str,
        sha256: str,
        user_id: str,
    ) -> FileResponse:
        """Confirm file upload after direct S3 upload."""
        files = get_files_collection()
        
        # Get file record
        file_doc = await files.find_one({"_id": file_id})
        if not file_doc:
            raise ValueError("File not found")
        
        if file_doc["owner_id"] != user_id:
            raise PermissionError("Not authorized to confirm this upload")
        
        if file_doc["confirmed"]:
            raise ValueError("File already confirmed")
        
        # Verify file exists in S3
        s3_client = get_s3_client()
        if not s3_client.check_object_exists(file_doc["s3_key"]):
            # Delete the record since upload failed
            await files.delete_one({"_id": file_id})
            raise ValueError("File not found in storage. Upload may have failed.")
        
        # Update file record
        await files.update_one(
            {"_id": file_id},
            {"$set": {"confirmed": True, "sha256": sha256}},
        )
        
        return FileResponse(
            id=file_doc["_id"],
            filename=file_doc["filename"],
            content_type=file_doc["content_type"],
            size=file_doc["size"],
            directory_id=file_doc["directory_id"],
            created_at=file_doc["created_at"],
        )

    @staticmethod
    async def get_download_url(
        file_id: str,
    ) -> FileDownloadResponse:
        """Get presigned URL for file download."""
        files = get_files_collection()
        
        file_doc = await files.find_one({"_id": file_id, "confirmed": True})
        if not file_doc:
            raise ValueError("File not found")
        
        s3_client = get_s3_client()
        presigned_url = s3_client.generate_presigned_get_url(
            key=file_doc["s3_key"],
            expires_in=3600,
            filename=file_doc["filename"],
        )
        
        return FileDownloadResponse(
            presigned_url=presigned_url,
            filename=file_doc["filename"],
            expires_in=3600,
        )

    @staticmethod
    async def get_preview_url(
        file_id: str,
    ) -> FileDownloadResponse:
        """Get presigned URL for file preview (inline)."""
        files = get_files_collection()
        
        file_doc = await files.find_one({"_id": file_id, "confirmed": True})
        if not file_doc:
            raise ValueError("File not found")
        
        s3_client = get_s3_client()
        presigned_url = s3_client.generate_presigned_get_url(
            key=file_doc["s3_key"],
            expires_in=3600,
            filename=file_doc["filename"],
            content_disposition="inline",
        )
        
        return FileDownloadResponse(
            presigned_url=presigned_url,
            filename=file_doc["filename"],
            expires_in=3600,
        )

    @staticmethod
    async def delete_file(
        file_id: str,
        user_id: str,
        user_role: UserRole = UserRole.USER,
    ) -> bool:
        """Delete a file."""
        files = get_files_collection()
        
        file_doc = await files.find_one({"_id": file_id})
        if not file_doc:
            return False
        
        if file_doc["owner_id"] != user_id and user_role != UserRole.SUPER_ADMIN:
            raise PermissionError("Not authorized to delete this file")
        
        # Delete from S3
        s3_client = get_s3_client()
        s3_client.delete_object(file_doc["s3_key"])
        
        # Delete from database
        await files.delete_one({"_id": file_id})
        
        return True

    @staticmethod
    async def list_files(directory_id: str) -> List[FileResponse]:
        """List all confirmed files in a directory."""
        files = get_files_collection()
        
        cursor = files.find({
            "directory_id": directory_id,
            "confirmed": True,
        })
        
        result = []
        async for file_doc in cursor:
            result.append(FileResponse(
                id=file_doc["_id"],
                filename=file_doc["filename"],
                content_type=file_doc["content_type"],
                size=file_doc["size"],
                directory_id=file_doc["directory_id"],
                created_at=file_doc["created_at"],
            ))
        
        return result

    @staticmethod
    async def get_file(file_id: str) -> Optional[dict]:
        """Get file document."""
        files = get_files_collection()
        return await files.find_one({"_id": file_id, "confirmed": True})


file_service = FileService()
