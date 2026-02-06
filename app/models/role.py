from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    PENDING = "pending"


# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        "read": True,
        "write": True,
        "delete": True,
        "manage_users": True,
        "access_all": True,  # Can access all directories
    },
    UserRole.ADMIN: {
        "read": True,
        "write": True,
        "delete": True,
        "manage_users": True,
        "access_all": False,
    },
    UserRole.USER: {
        "read": True,
        "write": True,
        "delete": False,
        "manage_users": False,
        "access_all": False,
    },
    UserRole.PENDING: {
        "read": False,
        "write": False,
        "delete": False,
        "manage_users": False,
        "access_all": False,
    },
}


def get_role_permissions(role: UserRole) -> dict:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[UserRole.USER])


def has_permission(role: UserRole, permission: str) -> bool:
    """Check if a role has a specific permission."""
    permissions = get_role_permissions(role)
    return permissions.get(permission, False)


def is_super_admin(role: UserRole) -> bool:
    """Check if role is super_admin."""
    return role == UserRole.SUPER_ADMIN
