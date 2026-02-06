from typing import List
from fastapi import APIRouter, HTTPException, status, Depends

from app.models.permission import PermissionGrant, PermissionResponse, PermissionListResponse
from app.models.user import UserResponse
from app.services.permission_service import permission_service
from app.services.directory_service import directory_service
from app.api.deps import get_current_user


router = APIRouter(prefix="/directories", tags=["Permissions"])


@router.post("/{directory_id}/permissions", response_model=PermissionResponse)
async def grant_permission(
    directory_id: str,
    data: PermissionGrant,
    current_user: UserResponse = Depends(get_current_user),
):
    """Grant permissions to a user for a directory."""
    # Check if user is owner
    is_owner = await directory_service.is_owner(directory_id, current_user.id)
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only directory owner can manage permissions",
        )
    
    try:
        return await permission_service.grant_permission(
            data=data,
            directory_id=directory_id,
            granted_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete("/{directory_id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    directory_id: str,
    user_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Revoke permissions from a user for a directory."""
    try:
        success = await permission_service.revoke_permission(
            directory_id=directory_id,
            user_id=user_id,
            revoked_by=current_user.id,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get("/{directory_id}/permissions", response_model=PermissionListResponse)
async def list_permissions(
    directory_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """List all permissions for a directory."""
    # Check if user is owner
    is_owner = await directory_service.is_owner(directory_id, current_user.id)
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only directory owner can view permissions",
        )
    
    permissions = await permission_service.get_directory_permissions(directory_id)
    return PermissionListResponse(
        permissions=permissions,
        directory_id=directory_id,
    )
