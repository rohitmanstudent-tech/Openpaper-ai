from fastapi import Depends

from app.core.exceptions import PermissionDeniedError
from app.core.security import get_current_user
from app.models import User, UserRole

PERMISSIONS = {
    "manage_users": [UserRole.ADMIN],
    "view_users": [UserRole.ADMIN, UserRole.MANAGER],
    "manage_agents": [UserRole.ADMIN, UserRole.MANAGER],
    "create_agents": [UserRole.ADMIN, UserRole.MANAGER, UserRole.MEMBER],
    "view_agents": [UserRole.ADMIN, UserRole.MANAGER, UserRole.MEMBER, UserRole.VIEWER],
    "manage_settings": [UserRole.ADMIN],
    "view_analytics": [UserRole.ADMIN, UserRole.MANAGER],
}


def require_permission(permission: str):
    async def checker(current_user: User = Depends(get_current_user)):
        allowed_roles = PERMISSIONS.get(permission, [])
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(f"Missing permission: {permission}")
        return current_user
    return checker
