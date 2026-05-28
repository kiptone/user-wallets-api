"""
Configuration module for the application.
Uses Pydantic Settings to load environment variables safely.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        db_host: PostgreSQL host
        db_port: PostgreSQL port
        db_name: Database name
        db_user: Database user
        db_password: Database password
        database_url: Full async PostgreSQL connection string
        app_env: Application environment (development, testing, production)
        debug: Debug mode flag
    """

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "wallets_db"
    db_user: str = "postgres"
    db_password: str = "postgres123"
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres123@localhost:5432/wallets_db"
    )
    app_env: str = "development"
    debug: bool = True

    class Config:
        """Pydantic configuration"""

        env_file = ".env"
        case_sensitive = False


settings = Settings()
