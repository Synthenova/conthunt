"""User role schemas and enums."""
from enum import Enum
from pydantic import BaseModel


class UserRole(str, Enum):
    """User subscription tiers."""
    FREE = "free"
    CREATOR = "creator"
    PRO_RESEARCH = "pro_research"


class UserRoleUpdate(BaseModel):
    """Request body for role update webhook."""
    firebase_uid: str
    new_role: UserRole


class UserInfo(BaseModel):
    """User info with role."""
    id: str  # UUID as string
    firebase_uid: str
    role: UserRole
