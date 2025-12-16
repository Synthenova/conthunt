"""Role-based access control dependencies."""
from typing import Callable

from fastapi import Depends, HTTPException

from app.auth.firebase import get_current_user, AuthUser
from app.schemas.roles import UserRole


def require_role(*allowed_roles: UserRole) -> Callable:
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/pro-feature")
        async def pro_feature(user: AuthUser = Depends(require_role(UserRole.PRO_RESEARCH))):
            ...
    """
    allowed = {r.value for r in allowed_roles}
    
    def dependency(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=403, 
                detail=f"This feature requires one of: {list(allowed)}"
            )
        return user
    
    return dependency


# Convenience dependencies
require_creator = require_role(UserRole.CREATOR, UserRole.PRO_RESEARCH)
require_pro = require_role(UserRole.PRO_RESEARCH)
