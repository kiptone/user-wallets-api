"""Test configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text
from httpx import AsyncClient

from app.main import app
from app.database import get_db
from app.models import Base
from app.config import settings

# Use a test database URL - SQLite for simplicity, or a separate PostgreSQL instance
# For production, use a separate test PostgreSQL database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
# Uncomment below for PostgreSQL test database
# TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres123@localhost/test_wallets_db"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine):
    """Create test database session."""
    async_session_local = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_local() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(test_db_session):
    """Create async HTTP client for testing."""

    async def override_get_db():
        """Override database dependency with test database session."""
        yield test_db_session

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def clean_db(test_db_session):
    """Clean database before each test."""
    # Delete all records
    from app.models import Wallet

    await test_db_session.execute("DELETE FROM wallets")
    await test_db_session.commit()
    yield test_db_session


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.

    This is required for pytest-asyncio to work correctly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
