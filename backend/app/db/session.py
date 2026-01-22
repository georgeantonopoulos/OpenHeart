"""
Database session management for OpenHeart Cyprus.

Provides async SQLAlchemy session handling with connection pooling.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields an async session and ensures proper cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def set_tenant_context(session: AsyncSession, clinic_id: int) -> None:
    """
    Set PostgreSQL session variable for Row-Level Security.

    This must be called before any queries to patient data
    to ensure RLS policies filter correctly.

    Args:
        session: The database session
        clinic_id: The clinic ID for tenant isolation
    """
    await session.execute(
        text(f"SET app.clinic_id = '{clinic_id}'")
    )


async def set_user_context(session: AsyncSession, user_id: int) -> None:
    """
    Set PostgreSQL session variable for audit tracking.

    Args:
        session: The database session
        user_id: The current user ID
    """
    await session.execute(
        text(f"SET app.user_id = '{user_id}'")
    )
