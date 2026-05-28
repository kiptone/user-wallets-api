"""
SQLAlchemy models for database tables.
"""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DECIMAL, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Wallet(Base):
    """
    Wallet model representing user wallet in the system.

    Attributes:
        id: UUID primary key
        balance: Current wallet balance (stored as DECIMAL for precision)
        created_at: Timestamp of wallet creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="Unique wallet identifier (UUID)",
    )

    balance: Mapped[Decimal] = mapped_column(
        DECIMAL(18, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Current wallet balance with 2 decimal places",
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When wallet was created",
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When wallet was last updated",
    )

    def __repr__(self) -> str:
        return (
            f"<Wallet(id={self.id}, balance={self.balance}, "
            f"updated_at={self.updated_at})>"
        )
