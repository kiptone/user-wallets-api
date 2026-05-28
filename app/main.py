"""
Main FastAPI application.
Entry point for the Wallet API server.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.wallets import router as wallets_router
from app.config import settings
from app.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Runs on startup and shutdown.

    On startup:
    - Initialize database tables
    - Apply pending migrations

    On shutdown:
    - Close database connections
    """
    # Startup
    logger.info("Starting application...")
    try:
        # Check database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("✓ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="User Wallets API",
    description="REST API for managing user wallets with concurrent transaction support",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(wallets_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/", tags=["info"])
async def root() -> dict:
    """
    Root endpoint with API information.
    Returns:
        dict: API info and links to documentation
    """
    return {
        "name": "User Wallets API",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
