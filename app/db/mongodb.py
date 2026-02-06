from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from app.core.config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB."""
    mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
    mongodb.db = mongodb.client[settings.mongodb_db_name]
    
    # Create indexes
    await create_indexes()
    
    print(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def close_mongodb_connection():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create database indexes."""
    if mongodb.db is None:
        return
    
    # Users collection indexes
    await mongodb.db.users.create_index("email", unique=True)
    
    # Directories collection indexes
    await mongodb.db.directories.create_index("owner_id")
    await mongodb.db.directories.create_index("parent_id")
    await mongodb.db.directories.create_index([("owner_id", 1), ("path", 1)])
    
    # Files collection indexes
    await mongodb.db.files.create_index("directory_id")
    await mongodb.db.files.create_index("owner_id")
    await mongodb.db.files.create_index("s3_key", unique=True)
    
    # Permissions collection indexes
    await mongodb.db.permissions.create_index([("user_id", 1), ("directory_id", 1)], unique=True)
    await mongodb.db.permissions.create_index("directory_id")
    
    # Token blacklist indexes
    await mongodb.db.token_blacklist.create_index("token", unique=True)
    await mongodb.db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if mongodb.db is None:
        raise RuntimeError("Database not initialized")
    return mongodb.db


# Collection getters
def get_users_collection():
    return get_database().users


def get_directories_collection():
    return get_database().directories


def get_files_collection():
    return get_database().files


def get_permissions_collection():
    return get_database().permissions


def get_token_blacklist_collection():
    return get_database().token_blacklist
