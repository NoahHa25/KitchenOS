"""feat(pricing): add recipe pricing fields

Revision ID: cbdf5f2b82e2
Revises: ee88fc87f4ee
Create Date: 2026-09-20 14:14:37.112207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "cbdf5f2b82e2"
down_revision: Union[str, Sequence[str], None] = "ee88fc87f4ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "recipes",
        sa.Column(
            "selling_price",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
    )

    op.add_column(
        "recipes",
        sa.Column(
            "portion_size",
            sa.Float(),
            server_default="1",
            nullable=False,
        ),
    )

    op.add_column(
        "recipes",
        sa.Column(
            "portion_unit",
            sa.String(length=20),
            server_default="portion",
            nullable=False,
        ),
    )

    op.add_column(
        "recipes",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
    )

    op.alter_column(
        "recipes",
        "description",
        existing_type=sa.VARCHAR(length=500),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "recipes",
        "description",
        existing_type=sa.String(length=1000),
        type_=sa.VARCHAR(length=500),
        existing_nullable=True,
    )

    op.drop_column("recipes", "is_active")
    op.drop_column("recipes", "portion_unit")
    op.drop_column("recipes", "portion_size")
    op.drop_column("recipes", "selling_price")