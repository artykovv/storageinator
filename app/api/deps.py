from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.services.auth_service import auth_service
from app.services.permission_service import permission_service
from app.services.directory_service import directory_service
from app.models.user import UserResponse
from app.models.permission import PermissionType
from app.models.role import UserRole, has_permission
from app.db.mongodb import get_token_blacklist_collection


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    # Check if token is blacklisted
    blacklist = get_token_blacklist_collection()
    if await blacklist.find_one({"token": token}):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    # Get user
    user = await auth_service.get_user_by_id(payload.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[UserResponse]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Require admin or super_admin role."""
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_super_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Require super_admin role."""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


class PermissionChecker:
    """Dependency class for checking permissions."""
    
    def __init__(self, permission_type: PermissionType):
        self.permission_type = permission_type
    
    async def __call__(
        self,
        directory_id: str,
        current_user: UserResponse = Depends(get_current_user),
    ) -> bool:
        """Check if current user has required permission."""
        # Super admin always has all permissions
        if current_user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Check if directory is public (for read/write permissions)
        if self.permission_type in (PermissionType.READ, PermissionType.WRITE):
            is_public = await directory_service.is_public(directory_id)
            if is_public:
                return True
        
        # Admins have all permissions on their own directories
        if current_user.role == UserRole.ADMIN:
            is_owner = await directory_service.is_owner(directory_id, current_user.id)
            if is_owner:
                return True
        
        # Check role-based permissions first
        permission_name = self.permission_type.value
        if not has_permission(current_user.role, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your role does not have {permission_name} permission",
            )
        
        # Check if owner
        is_owner = await directory_service.is_owner(directory_id, current_user.id)
        if is_owner:
            return True
        
        # Then check directory-specific permissions (shared)
        has_perm = await permission_service.check_permission(
            user_id=current_user.id,
            directory_id=directory_id,
            permission_type=self.permission_type,
        )
        
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing {permission_name} permission for this directory",
            )
        
        return True


# Pre-configured permission checkers
require_read = PermissionChecker(PermissionType.READ)
require_write = PermissionChecker(PermissionType.WRITE)
require_delete = PermissionChecker(PermissionType.DELETE)
