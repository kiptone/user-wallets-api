"""Create wallets table

Revision ID: 001_create_wallets
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_create_wallets"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create wallets table with UUID primary key and DECIMAL balance."""
    # Create wallets table
    op.create_table(
        "wallets",
        sa.Column(
            "id",
            sa.String(),
            server_default=sa.text("gen_random_uuid()::text"),
            nullable=False,
        ),
        sa.Column(
            "balance",
            sa.DECIMAL(precision=18, scale=2),
            server_default=sa.text("'0.00'::numeric"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on created_at for potential filtering by date
    op.create_index("ix_wallets_created_at", "wallets", ["created_at"], unique=False)


def downgrade() -> None:
    """Drop wallets table."""
    op.drop_index("ix_wallets_created_at", table_name="wallets")
    op.drop_table("wallets")
