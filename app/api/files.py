from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.file import (
    FileUploadRequest,
    FileUploadResponse,
    FileConfirm,
    FileResponse,
    FileDownloadResponse,
    FileListResponse,
    FileUpdate,
)
from app.models.user import UserResponse
from app.models.role import UserRole
from app.services.file_service import file_service
from app.services.directory_service import directory_service
from app.services.permission_service import permission_service
from app.models.permission import PermissionType
from app.api.deps import get_current_user


router = APIRouter(prefix="/files", tags=["Files"])


async def check_file_permission(
    user: UserResponse,
    directory_id: str,
    permission_type: PermissionType,
) -> bool:
    """Check if user has permission for directory, considering role and public status."""
    # Super admin has all permissions
    if user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Check if directory is public (read-only)
    if permission_type == PermissionType.READ:
        is_public = await directory_service.is_public(directory_id)
        if is_public:
            return True
    
    # Check if user is owner
    is_owner = await directory_service.is_owner(directory_id, user.id)
    if is_owner:
        return True
    
    # Check shared permissions
    return await permission_service.check_permission(
        user_id=user.id,
        directory_id=directory_id,
        permission_type=permission_type,
    )


@router.post("/upload-url", response_model=FileUploadResponse)
async def request_upload_url(
    data: FileUploadRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Request a presigned URL for file upload."""
    # Check write permission
    has_perm = await check_file_permission(
        current_user, data.directory_id, PermissionType.WRITE
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No write permission for this directory",
        )
    
    try:
        return await file_service.request_upload(
            data=data,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{file_id}/confirm", response_model=FileResponse)
async def confirm_upload(
    file_id: str,
    data: FileConfirm,
    current_user: UserResponse = Depends(get_current_user),
):
    """Confirm file upload after direct S3 upload."""
    try:
        return await file_service.confirm_upload(
            file_id=file_id,
            sha256=data.sha256,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            detail=str(e),
        )


@router.get("/{file_id}/preview-url", response_model=FileDownloadResponse)
async def get_preview_url(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a presigned URL for file preview (inline)."""
    # Get file to check directory
    file_doc = await file_service.get_file(file_id)
    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Check read permission
    has_perm = await check_file_permission(
        current_user, file_doc["directory_id"], PermissionType.READ
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No read permission for this file",
        )
    
    try:
        return await file_service.get_preview_url(file_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{file_id}/download-url", response_model=FileDownloadResponse)
async def get_download_url(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a presigned URL for file download."""
    # Get file to check directory
    file_doc = await file_service.get_file(file_id)
    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Check read permission
    has_perm = await check_file_permission(
        current_user, file_doc["directory_id"], PermissionType.READ
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No read permission for this file",
        )
    
    try:
        return await file_service.get_download_url(file_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: str,
    data: FileUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update file status (e.g. is_public)."""
    # Get file to check directory/owner
    file_doc = await file_service.get_file(file_id)
    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Check write permission (owner or super_admin)
    if current_user.role != UserRole.SUPER_ADMIN:
        is_owner = await directory_service.is_owner(file_doc["directory_id"], current_user.id)
        if not is_owner:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can change public status",
            )
    
    updated_file = await file_service.update_file(
        file_id=file_id,
        update_data=data,
        user_id=current_user.id,
    )
    if not updated_file:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return updated_file


async def delete_file(
    file_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a file."""
    # Get file to check directory
    file_doc = await file_service.get_file(file_id)
    if not file_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Check delete permission (super_admin or owner)
    if current_user.role != UserRole.SUPER_ADMIN:
        is_owner = await directory_service.is_owner(file_doc["directory_id"], current_user.id)
        if not is_owner:
            has_perm = await permission_service.check_permission(
                user_id=current_user.id,
                directory_id=file_doc["directory_id"],
                permission_type=PermissionType.DELETE,
            )
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No delete permission for this file",
                )
    
    try:
        success = await file_service.delete_file(
            file_id=file_id,
            user_id=current_user.id,
            user_role=current_user.role,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/directory/{directory_id}", response_model=FileListResponse)
async def list_files(
    directory_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """List all files in a directory."""
    # Check read permission
    has_perm = await check_file_permission(
        current_user, directory_id, PermissionType.READ
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No read permission for this directory",
        )
    
    files = await file_service.list_files(directory_id)
    return FileListResponse(files=files, total=len(files))
