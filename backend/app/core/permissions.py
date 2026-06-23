from enum import Enum
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.core.security import get_current_user


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


PERMISSION_HIERARCHY = {
    Role.ADMIN: 100,
    Role.MANAGER: 80,
    Role.MEMBER: 50,
    Role.VIEWER: 10,
}

PERMISSIONS = {
    "agents:create": [Role.ADMIN, Role.MANAGER],
    "agents:read": [Role.ADMIN, Role.MANAGER, Role.MEMBER, Role.VIEWER],
    "agents:update": [Role.ADMIN, Role.MANAGER],
    "agents:delete": [Role.ADMIN],
    "agents:chat": [Role.ADMIN, Role.MANAGER, Role.MEMBER],
    "memory:read": [Role.ADMIN, Role.MANAGER, Role.MEMBER, Role.VIEWER],
    "memory:write": [Role.ADMIN, Role.MANAGER, Role.MEMBER],
    "memory:delete": [Role.ADMIN, Role.MANAGER],
    "tasks:create": [Role.ADMIN, Role.MANAGER],
    "tasks:read": [Role.ADMIN, Role.MANAGER, Role.MEMBER, Role.VIEWER],
    "tasks:update": [Role.ADMIN, Role.MANAGER],
    "tasks:delete": [Role.ADMIN],
    "users:manage": [Role.ADMIN],
    "settings:read": [Role.ADMIN, Role.MANAGER],
    "settings:write": [Role.ADMIN],
}


def require_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        allowed_roles = PERMISSIONS.get(permission, [])
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return current_user
    return permission_checker
