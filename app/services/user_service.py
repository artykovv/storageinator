from typing import Optional, List
from bson import ObjectId

from app.db.mongodb import get_users_collection
from app.models.user import UserResponse, UserUpdate
from app.models.role import UserRole


class UserService:
    """Service for user management operations (admin)."""

    @staticmethod
    async def list_users(skip: int = 0, limit: int = 50) -> List[UserResponse]:
        """List all users."""
        users = get_users_collection()
        cursor = users.find().skip(skip).limit(limit)
        
        result = []
        async for user in cursor:
            result.append(UserResponse(
                id=user["_id"],
                email=user["email"],
                role=UserRole(user.get("role", "user")),
                is_active=user.get("is_active", True),
                created_at=user["created_at"],
            ))
        return result

    @staticmethod
    async def get_user(user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        users = get_users_collection()
        user = await users.find_one({"_id": user_id})
        
        if not user:
            return None
        
        return UserResponse(
            id=user["_id"],
            email=user["email"],
            role=UserRole(user.get("role", "user")),
            is_active=user.get("is_active", True),
            created_at=user["created_at"],
        )

    @staticmethod
    async def update_user(user_id: str, update_data: UserUpdate) -> Optional[UserResponse]:
        """Update user role, status, email or password."""
        users = get_users_collection()
        
        # Build update document
        update_doc = {}
        if update_data.role is not None:
            update_doc["role"] = update_data.role.value
        if update_data.is_active is not None:
            update_doc["is_active"] = update_data.is_active
        if update_data.email is not None:
            # Check if email is taken by another user
            existing = await users.find_one({"email": update_data.email})
            if existing and existing["_id"] != user_id:
                raise ValueError("Email already exists")
            update_doc["email"] = update_data.email
        if update_data.password is not None:
            from app.core.security import get_password_hash
            update_doc["hashed_password"] = get_password_hash(update_data.password)
        
        if not update_doc:
            return await UserService.get_user(user_id)
        
        result = await users.update_one(
            {"_id": user_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            return None
        
        return await UserService.get_user(user_id)

    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete user."""
        users = get_users_collection()
        result = await users.delete_one({"_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    async def count_users() -> int:
        """Count total users."""
        users = get_users_collection()
        return await users.count_documents({})


user_service = UserService()
