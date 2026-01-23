"""
Redis utilities for OpenHeart Cyprus.

Provides token blacklisting and session invalidation via Redis.
Keys auto-expire to match token lifetimes — no manual cleanup needed.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Redis key prefixes
BLACKLIST_PREFIX = "token:blacklist:"
USER_INVALIDATION_PREFIX = "user:invalidated:"


async def get_redis(request: Request) -> Redis:
    """
    FastAPI dependency to get Redis client from app state.

    Usage:
        redis = await get_redis(request)
        # or via Depends:
        redis: Redis = Depends(get_redis)
    """
    return request.app.state.redis


async def blacklist_token(redis: Redis, jti: str, ttl_seconds: int) -> None:
    """
    Add a token JTI to the blacklist with TTL matching token expiry.

    The key auto-expires after the token would have expired anyway,
    so no cleanup is needed.

    Args:
        redis: Redis client
        jti: JWT ID to blacklist
        ttl_seconds: Remaining lifetime of the token in seconds
    """
    if not jti or ttl_seconds <= 0:
        return
    key = f"{BLACKLIST_PREFIX}{jti}"
    await redis.set(key, "1", ex=ttl_seconds)
    logger.info(f"Token {jti[:8]}... blacklisted for {ttl_seconds}s")


async def is_token_blacklisted(redis: Redis, jti: str) -> bool:
    """
    Check if a token JTI has been blacklisted.

    Args:
        redis: Redis client
        jti: JWT ID to check

    Returns:
        True if token is blacklisted
    """
    if not jti:
        return False
    key = f"{BLACKLIST_PREFIX}{jti}"
    return await redis.exists(key) > 0


async def invalidate_user_sessions(
    redis: Redis, user_id: int, timestamp: Optional[datetime] = None
) -> None:
    """
    Store a timestamp after which all tokens for a user are invalid.

    Any token with iat < this timestamp will be rejected by get_current_user().
    The key expires after 7 days (max refresh token lifetime), after which
    no valid pre-invalidation tokens can exist.

    Args:
        redis: Redis client
        user_id: User whose sessions to invalidate
        timestamp: Invalidation cutoff (defaults to now)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    key = f"{USER_INVALIDATION_PREFIX}{user_id}"
    await redis.set(key, timestamp.isoformat(), ex=7 * 24 * 3600)
    logger.info(f"User {user_id} sessions invalidated from {timestamp.isoformat()}")


async def get_user_invalidation_time(redis: Redis, user_id: int) -> Optional[datetime]:
    """
    Get the timestamp after which a user's tokens are invalid.

    Args:
        redis: Redis client
        user_id: User ID to check

    Returns:
        Invalidation datetime if set, None otherwise
    """
    key = f"{USER_INVALIDATION_PREFIX}{user_id}"
    value = await redis.get(key)
    if value:
        return datetime.fromisoformat(value)
    return None
