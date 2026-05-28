"""
Database module for async PostgreSQL connection.
Uses SQLAlchemy 2.0 with asyncio support and asyncpg driver.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Create async engine with asyncpg driver
# pool_size: max connections in the pool (default 5)
# max_overflow: additional connections if pool is exhausted (default 10)
# echo=True logs all SQL queries (disable in production)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Check connection is alive before using
)

# Create async session factory
# expire_on_commit=False: objects remain accessible after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    FastAPI will call this automatically for each request.

    Usage in endpoint:
        async def my_endpoint(session: AsyncSession = Depends(get_db)):
            # session is automatically injected and closed after response

    Yields:
        AsyncSession: Database session for the request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
