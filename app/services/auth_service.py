from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from app.db.mongodb import get_users_collection, get_token_blacklist_collection
from app.core.security import (
    get_password_hash,
    verify_password,
    create_tokens,
    decode_token,
)
from app.models.user import UserCreate, UserResponse
from app.models.auth import Token
from app.models.role import UserRole


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    async def register_user(user_data: UserCreate, role: UserRole = UserRole.PENDING) -> UserResponse:
        """Register a new user."""
        users = get_users_collection()
        
        # Check if user already exists
        existing = await users.find_one({"email": user_data.email})
        if existing:
            raise ValueError("User with this email already exists")
        
        # Create user document
        user_doc = {
            "_id": str(ObjectId()),
            "email": user_data.email,
            "hashed_password": get_password_hash(user_data.password),
            "role": role.value,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        
        await users.insert_one(user_doc)
        
        return UserResponse(
            id=user_doc["_id"],
            email=user_doc["email"],
            role=role,
            is_active=True,
            created_at=user_doc["created_at"],
        )

    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Token]:
        """Authenticate user and return tokens."""
        users = get_users_collection()
        
        user = await users.find_one({"email": email})
        if not user:
            return None
        
        # Check if user is active
        if not user.get("is_active", True):
            return None
        
        # Check if user is pending
        if user.get("role") == UserRole.PENDING:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        access_token, refresh_token = create_tokens(user["_id"])
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token."""
        # Check if token is blacklisted
        blacklist = get_token_blacklist_collection()
        if await blacklist.find_one({"token": refresh_token}):
            return None
        
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.type != "refresh":
            return None
        
        # Check if user still exists and is active
        users = get_users_collection()
        user = await users.find_one({"_id": payload.sub})
        if not user or not user.get("is_active", True):
            return None
        
        # Create new tokens
        access_token, new_refresh_token = create_tokens(payload.sub)
        
        # Blacklist old refresh token
        await blacklist.insert_one({
            "token": refresh_token,
            "expires_at": payload.exp,
        })
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    @staticmethod
    async def logout(token: str) -> bool:
        """Logout user by blacklisting token."""
        payload = decode_token(token)
        if not payload:
            return False
        
        blacklist = get_token_blacklist_collection()
        try:
            await blacklist.insert_one({
                "token": token,
                "expires_at": payload.exp,
            })
            return True
        except Exception:
            return False

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[UserResponse]:
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
    async def get_user_by_email(email: str) -> Optional[dict]:
        """Get user by email (internal use)."""
        users = get_users_collection()
        return await users.find_one({"email": email})

    @staticmethod
    async def create_admin_user(email: str, password: str) -> Optional[UserResponse]:
        """Create super admin user if not exists."""
        existing = await AuthService.get_user_by_email(email)
        if existing:
            print(f"Admin user already exists: {email}")
            return None
        
        user_data = UserCreate(email=email, password=password)
        user = await AuthService.register_user(user_data, role=UserRole.SUPER_ADMIN)
        print(f"Created super admin user: {email}")
        return user


auth_service = AuthService()
