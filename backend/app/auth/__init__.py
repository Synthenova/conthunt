"""Auth package initialization."""
from .firebase import get_current_user, init_firebase

__all__ = ["get_current_user", "init_firebase"]
