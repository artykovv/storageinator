from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.deps import require_admin
from app.models.user import UserResponse, UserUpdate
from app.services.user_service import user_service


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: UserResponse = Depends(require_admin),
):
    """List all users (admin only)."""
    return await user_service.list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: UserResponse = Depends(require_admin),
):
    """Get user by ID (admin only)."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    admin: UserResponse = Depends(require_admin),
):
    """Update user (admin only). Super admin can update everything."""
    # Prevent admin from deactivating themselves
    if user_id == admin.id and update_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    # Check permission for email/password updates
    if update_data.email is not None or update_data.password is not None:
        from app.models.role import UserRole
        if admin.role != UserRole.SUPER_ADMIN:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin can update email or password",
            )
    
    user = await user_service.update_user(user_id, update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: UserResponse = Depends(require_admin),
):
    """Delete user (admin only)."""
    # Prevent admin from deleting themselves
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {"message": "User deleted"}
