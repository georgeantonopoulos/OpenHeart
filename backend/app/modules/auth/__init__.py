"""
Authentication module for OpenHeart Cyprus.

Provides login, token refresh, and session management endpoints.
"""

from app.modules.auth.router import router

__all__ = ["router"]
