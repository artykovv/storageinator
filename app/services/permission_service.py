from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId

from app.db.mongodb import get_permissions_collection, get_directories_collection, get_users_collection
from app.models.permission import PermissionType, PermissionGrant, PermissionResponse


class PermissionService:
    """Service for permission operations."""

    @staticmethod
    async def grant_permission(
        data: PermissionGrant,
        directory_id: str,
        granted_by: str,
    ) -> PermissionResponse:
        """Grant permissions to a user for a directory."""
        permissions = get_permissions_collection()
        users = get_users_collection()
        directories = get_directories_collection()
        
        # Check directory exists
        directory = await directories.find_one({"_id": directory_id})
        if not directory:
            raise ValueError("Directory not found")
        
        # Check granter is owner
        if directory["owner_id"] != granted_by:
            raise PermissionError("Only directory owner can grant permissions")
        
        # Get user by email
        user = await users.find_one({"email": data.user_email})
        if not user:
            raise ValueError("User not found")
        
        user_id = user["_id"]
        
        # Can't grant permissions to self
        if user_id == granted_by:
            raise ValueError("Cannot grant permissions to yourself")
        
        # Check if permission already exists
        existing = await permissions.find_one({
            "user_id": user_id,
            "directory_id": directory_id,
        })
        
        if existing:
            # Update existing permission
            await permissions.update_one(
                {"_id": existing["_id"]},
                {"$set": {"permissions": [p.value for p in data.permissions]}},
            )
            perm_id = existing["_id"]
        else:
            # Create new permission
            perm_doc = {
                "_id": str(ObjectId()),
                "user_id": user_id,
                "directory_id": directory_id,
                "permissions": [p.value for p in data.permissions],
                "granted_by": granted_by,
                "created_at": datetime.now(timezone.utc),
            }
            await permissions.insert_one(perm_doc)
            perm_id = perm_doc["_id"]
        
        # Get updated permission
        perm = await permissions.find_one({"_id": perm_id})
        
        return PermissionResponse(
            id=perm["_id"],
            user_id=perm["user_id"],
            user_email=data.user_email,
            directory_id=perm["directory_id"],
            permissions=[PermissionType(p) for p in perm["permissions"]],
            created_at=perm["created_at"],
        )

    @staticmethod
    async def revoke_permission(
        directory_id: str,
        user_id: str,
        revoked_by: str,
    ) -> bool:
        """Revoke all permissions for a user on a directory."""
        permissions = get_permissions_collection()
        directories = get_directories_collection()
        
        # Check directory exists and user is owner
        directory = await directories.find_one({"_id": directory_id})
        if not directory:
            raise ValueError("Directory not found")
        
        if directory["owner_id"] != revoked_by:
            raise PermissionError("Only directory owner can revoke permissions")
        
        result = await permissions.delete_one({
            "user_id": user_id,
            "directory_id": directory_id,
        })
        
        return result.deleted_count > 0

    @staticmethod
    async def get_directory_permissions(
        directory_id: str,
    ) -> List[PermissionResponse]:
        """Get all permissions for a directory."""
        permissions = get_permissions_collection()
        users = get_users_collection()
        
        cursor = permissions.find({"directory_id": directory_id})
        
        result = []
        async for perm in cursor:
            # Get user email
            user = await users.find_one({"_id": perm["user_id"]})
            user_email = user["email"] if user else "unknown"
            
            result.append(PermissionResponse(
                id=perm["_id"],
                user_id=perm["user_id"],
                user_email=user_email,
                directory_id=perm["directory_id"],
                permissions=[PermissionType(p) for p in perm["permissions"]],
                created_at=perm["created_at"],
            ))
        
        return result

    @staticmethod
    async def check_permission(
        user_id: str,
        directory_id: str,
        permission_type: PermissionType,
    ) -> bool:
        """Check if user has specific permission on directory (including inheritance)."""
        directories = get_directories_collection()
        permissions = get_permissions_collection()
        
        # Get directory
        directory = await directories.find_one({"_id": directory_id})
        if not directory:
            return False
        
        # Owner has all permissions
        if directory["owner_id"] == user_id:
            return True
        
        # Build path from directory to root
        path_ids = [directory_id]
        current = directory
        
        while current.get("parent_id"):
            path_ids.append(current["parent_id"])
            current = await directories.find_one({"_id": current["parent_id"]})
            if not current:
                break
        
        # Check permissions from most specific to least specific
        for dir_id in path_ids:
            perm = await permissions.find_one({
                "user_id": user_id,
                "directory_id": dir_id,
            })
            
            if perm:
                return permission_type.value in perm["permissions"]
        
        return False

    @staticmethod
    async def get_effective_permissions(
        user_id: str,
        directory_id: str,
    ) -> List[PermissionType]:
        """Get all effective permissions for user on directory."""
        directories = get_directories_collection()
        permissions = get_permissions_collection()
        
        # Get directory
        directory = await directories.find_one({"_id": directory_id})
        if not directory:
            return []
        
        # Owner has all permissions
        if directory["owner_id"] == user_id:
            return [PermissionType.READ, PermissionType.WRITE, PermissionType.DELETE]
        
        # Build path from directory to root
        path_ids = [directory_id]
        current = directory
        
        while current.get("parent_id"):
            path_ids.append(current["parent_id"])
            current = await directories.find_one({"_id": current["parent_id"]})
            if not current:
                break
        
        # Check permissions from most specific to least specific
        for dir_id in path_ids:
            perm = await permissions.find_one({
                "user_id": user_id,
                "directory_id": dir_id,
            })
            
            if perm:
                return [PermissionType(p) for p in perm["permissions"]]
        
        return []

    @staticmethod
    async def can_access_directory(
        user_id: str,
        directory_id: str,
    ) -> bool:
        """Check if user can access directory (owner or has any permission)."""
        directories = get_directories_collection()
        
        directory = await directories.find_one({"_id": directory_id})
        if not directory:
            return False
        
        # Owner can always access
        if directory["owner_id"] == user_id:
            return True
        
        # Check for any permission
        return await PermissionService.check_permission(
            user_id, directory_id, PermissionType.READ
        )


permission_service = PermissionService()
