from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId

from app.db.mongodb import get_directories_collection, get_files_collection, get_permissions_collection
from app.models.directory import DirectoryCreate, DirectoryResponse, DirectoryTree
from app.models.role import UserRole


class DirectoryService:
    """Service for directory operations."""

    @staticmethod
    async def create_directory(
        data: DirectoryCreate,
        owner_id: str,
    ) -> DirectoryResponse:
        """Create a new directory."""
        directories = get_directories_collection()
        
        # Build path
        if data.parent_id:
            parent = await directories.find_one({"_id": data.parent_id})
            if not parent:
                raise ValueError("Parent directory not found")
            path = f"{parent['path']}/{data.name}"
        else:
            path = f"/{data.name}"
        
        # Check for duplicate path for this user
        existing = await directories.find_one({
            "owner_id": owner_id,
            "path": path,
        })
        if existing:
            raise ValueError("Directory with this name already exists at this location")
        
        # Create directory document
        dir_doc = {
            "_id": str(ObjectId()),
            "name": data.name,
            "owner_id": owner_id,
            "parent_id": data.parent_id,
            "path": path,
            "is_public": data.is_public,
            "created_at": datetime.now(timezone.utc),
        }
        
        await directories.insert_one(dir_doc)
        
        return DirectoryResponse(
            id=dir_doc["_id"],
            name=dir_doc["name"],
            path=dir_doc["path"],
            parent_id=dir_doc["parent_id"],
            is_public=dir_doc["is_public"],
            owner_id=dir_doc["owner_id"],
            created_at=dir_doc["created_at"],
        )

    @staticmethod
    async def get_directory(directory_id: str) -> Optional[DirectoryResponse]:
        """Get a directory by ID."""
        directories = get_directories_collection()
        dir_doc = await directories.find_one({"_id": directory_id})
        
        if not dir_doc:
            return None
        
        return DirectoryResponse(
            id=dir_doc["_id"],
            name=dir_doc["name"],
            path=dir_doc["path"],
            parent_id=dir_doc.get("parent_id"),
            is_public=dir_doc.get("is_public", False),
            owner_id=dir_doc["owner_id"],
            created_at=dir_doc["created_at"],
        )

    @staticmethod
    async def get_user_directories(user_id: str, user_role: UserRole = UserRole.USER) -> List[DirectoryResponse]:
        """Get all directories accessible by user."""
        directories = get_directories_collection()
        permissions = get_permissions_collection()
        
        result = []
        
        # Super admin sees all directories
        if user_role == UserRole.SUPER_ADMIN:
            cursor = directories.find({})
            async for d in cursor:
                result.append(DirectoryResponse(
                    id=d["_id"],
                    name=d["name"],
                    path=d["path"],
                    parent_id=d.get("parent_id"),
                    is_public=d.get("is_public", False),
                    owner_id=d["owner_id"],
                    created_at=d["created_at"],
                ))
            return result
        
        # Get owned directories
        owned_cursor = directories.find({"owner_id": user_id})
        async for d in owned_cursor:
            result.append(DirectoryResponse(
                id=d["_id"],
                name=d["name"],
                path=d["path"],
                parent_id=d.get("parent_id"),
                is_public=d.get("is_public", False),
                owner_id=d["owner_id"],
                created_at=d["created_at"],
            ))
        
        result_ids = {r.id for r in result}
        
        # Get public directories
        public_cursor = directories.find({"is_public": True})
        async for d in public_cursor:
            if d["_id"] not in result_ids:
                result.append(DirectoryResponse(
                    id=d["_id"],
                    name=d["name"],
                    path=d["path"],
                    parent_id=d.get("parent_id"),
                    is_public=True,
                    owner_id=d["owner_id"],
                    created_at=d["created_at"],
                ))
                result_ids.add(d["_id"])
        
        # Get shared directories
        shared_perms = permissions.find({"user_id": user_id})
        shared_ids = [p["directory_id"] async for p in shared_perms]
        
        if shared_ids:
            shared_cursor = directories.find({"_id": {"$in": shared_ids}})
            async for d in shared_cursor:
                if d["_id"] not in result_ids:
                    result.append(DirectoryResponse(
                        id=d["_id"],
                        name=d["name"],
                        path=d["path"],
                        parent_id=d.get("parent_id"),
                        is_public=d.get("is_public", False),
                        owner_id=d["owner_id"],
                        created_at=d["created_at"],
                    ))
        
        return result

    @staticmethod
    async def get_directory_tree(user_id: str, user_role: UserRole = UserRole.USER) -> List[DirectoryTree]:
        """Get directory tree for user."""
        all_dirs = await DirectoryService.get_user_directories(user_id, user_role)
        
        # Build tree structure
        dir_map = {d.id: DirectoryTree(
            id=d.id,
            name=d.name,
            path=d.path,
            parent_id=d.parent_id,
            is_public=d.is_public,
            owner_id=d.owner_id,
            created_at=d.created_at,
            children=[],
        ) for d in all_dirs}
        
        roots = []
        for dir_tree in dir_map.values():
            if dir_tree.parent_id and dir_tree.parent_id in dir_map:
                dir_map[dir_tree.parent_id].children.append(dir_tree)
            else:
                roots.append(dir_tree)
        
        return roots

    @staticmethod
    async def update_directory(
        directory_id: str,
        user_id: str,
        user_role: UserRole,
        name: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[DirectoryResponse]:
        """Update directory."""
        directories = get_directories_collection()
        
        dir_doc = await directories.find_one({"_id": directory_id})
        if not dir_doc:
            return None
        
        # Check permission (owner or super_admin)
        if dir_doc["owner_id"] != user_id and user_role != UserRole.SUPER_ADMIN:
            raise PermissionError("Not authorized to update this directory")
        
        update_doc = {}
        if name is not None:
            update_doc["name"] = name
            # Update path
            if dir_doc.get("parent_id"):
                parent = await directories.find_one({"_id": dir_doc["parent_id"]})
                update_doc["path"] = f"{parent['path']}/{name}"
            else:
                update_doc["path"] = f"/{name}"
        
        if is_public is not None:
            update_doc["is_public"] = is_public
        
        if update_doc:
            await directories.update_one({"_id": directory_id}, {"$set": update_doc})
        
        return await DirectoryService.get_directory(directory_id)

    @staticmethod
    async def delete_directory(
        directory_id: str,
        user_id: str,
        user_role: UserRole = UserRole.USER,
        cascade: bool = False,
    ) -> bool:
        """Delete a directory."""
        directories = get_directories_collection()
        files = get_files_collection()
        permissions = get_permissions_collection()
        
        # Get directory
        dir_doc = await directories.find_one({"_id": directory_id})
        if not dir_doc:
            return False
        
        # Check ownership (super_admin can delete any)
        if dir_doc["owner_id"] != user_id and user_role != UserRole.SUPER_ADMIN:
            raise PermissionError("Not authorized to delete this directory")
        
        # Check for children
        children = await directories.find_one({"parent_id": directory_id})
        if children and not cascade:
            raise ValueError("Directory has subdirectories. Use cascade=true to delete all.")
        
        # Check for files
        has_files = await files.find_one({"directory_id": directory_id})
        if has_files and not cascade:
            raise ValueError("Directory has files. Use cascade=true to delete all.")
        
        if cascade:
            # Get all descendant directory IDs
            descendant_ids = await DirectoryService._get_descendant_ids(directory_id)
            all_ids = [directory_id] + descendant_ids
            
            # Delete all files in these directories
            await files.delete_many({"directory_id": {"$in": all_ids}})
            
            # Delete all permissions
            await permissions.delete_many({"directory_id": {"$in": all_ids}})
            
            # Delete all directories
            await directories.delete_many({"_id": {"$in": all_ids}})
        else:
            # Delete permissions
            await permissions.delete_many({"directory_id": directory_id})
            
            # Delete directory
            await directories.delete_one({"_id": directory_id})
        
        return True

    @staticmethod
    async def _get_descendant_ids(directory_id: str) -> List[str]:
        """Get all descendant directory IDs."""
        directories = get_directories_collection()
        result = []
        queue = [directory_id]
        
        while queue:
            parent_id = queue.pop(0)
            children_cursor = directories.find({"parent_id": parent_id})
            async for child in children_cursor:
                child_id = child["_id"]
                result.append(child_id)
                queue.append(child_id)
        
        return result

    @staticmethod
    async def is_owner(directory_id: str, user_id: str) -> bool:
        """Check if user is owner of directory."""
        directories = get_directories_collection()
        dir_doc = await directories.find_one({"_id": directory_id, "owner_id": user_id})
        return dir_doc is not None

    @staticmethod
    async def is_public(directory_id: str) -> bool:
        """Check if directory is public."""
        directories = get_directories_collection()
        dir_doc = await directories.find_one({"_id": directory_id})
        return dir_doc.get("is_public", False) if dir_doc else False


directory_service = DirectoryService()
