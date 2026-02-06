from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query

from app.models.directory import DirectoryCreate, DirectoryResponse, DirectoryTree, DirectoryUpdate
from app.models.user import UserResponse
from app.services.directory_service import directory_service
from app.services.permission_service import permission_service
from app.models.permission import PermissionType
from app.models.role import UserRole
from app.api.deps import get_current_user


router = APIRouter(prefix="/directories", tags=["Directories"])


@router.post("", response_model=DirectoryResponse, status_code=status.HTTP_201_CREATED)
async def create_directory(
    data: DirectoryCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Create a new directory."""
    # If parent_id is provided, check write permission
    if data.parent_id:
        # Super admin can create anywhere
        if current_user.role != UserRole.SUPER_ADMIN:
            # Check if parent is public or user has permission
            parent_dir = await directory_service.get_directory(data.parent_id)
            if parent_dir:
                # Even if public, only owner (or explicit write permission) can create subdirectories
                if parent_dir.owner_id != current_user.id:
                    has_permission = await permission_service.check_permission(
                        user_id=current_user.id,
                        directory_id=data.parent_id,
                        permission_type=PermissionType.WRITE,
                    )
                    if not has_permission:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="No write permission for parent directory",
                        )
    
    try:
        directory = await directory_service.create_directory(
            data=data,
            owner_id=current_user.id,
        )
        return directory
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[DirectoryTree])
async def get_directories(
    current_user: UserResponse = Depends(get_current_user),
):
    """Get directory tree for current user."""
    return await directory_service.get_directory_tree(current_user.id, current_user.role)


@router.get("/{directory_id}", response_model=DirectoryResponse)
async def get_directory(
    directory_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Get a specific directory."""
    directory = await directory_service.get_directory(directory_id)
    if not directory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Directory not found",
        )
    
    # Super admin can access all
    if current_user.role == UserRole.SUPER_ADMIN:
        return directory
    
    # Public directories accessible to all
    if directory.is_public:
        return directory
    
    # Owner can access
    if directory.owner_id == current_user.id:
        return directory
    
    # Check shared permissions
    can_access = await permission_service.can_access_directory(
        user_id=current_user.id,
        directory_id=directory_id,
    )
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this directory",
        )
    
    return directory


@router.patch("/{directory_id}", response_model=DirectoryResponse)
async def update_directory(
    directory_id: str,
    data: DirectoryUpdate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Update a directory (name, is_public)."""
    try:
        directory = await directory_service.update_directory(
            directory_id=directory_id,
            user_id=current_user.id,
            user_role=current_user.role,
            name=data.name,
            is_public=data.is_public,
        )
        if not directory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Directory not found",
            )
        return directory
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete("/{directory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_directory(
    directory_id: str,
    cascade: bool = Query(False, description="Delete all subdirectories and files"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Delete a directory."""
    try:
        success = await directory_service.delete_directory(
            directory_id=directory_id,
            user_id=current_user.id,
            user_role=current_user.role,
            cascade=cascade,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Directory not found",
            )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
