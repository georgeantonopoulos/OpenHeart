"""
Shared dependencies for OpenHeart Cyprus.
"""

from app.core.security import get_current_user
from app.core.permissions import require_permission, require_any_permission, require_all_permissions

__all__ = [
    "get_current_user",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
]
