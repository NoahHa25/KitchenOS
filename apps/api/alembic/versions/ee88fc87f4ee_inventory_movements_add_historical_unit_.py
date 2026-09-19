"""inventory movements add historical unit cost

Revision ID: ee88fc87f4ee
Revises: 91b4cb3c2b62
Create Date: 2026-09-19 21:04:42.289101

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ee88fc87f4ee"
down_revision: Union[str, Sequence[str], None] = "91b4cb3c2b62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add the new column as nullable first so existing rows
    # can be populated safely.
    op.add_column(
        "inventory_movements",
        sa.Column(
            "unit_cost",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
    )

    # Existing movements did not store historical unit cost.
    # For those rows, use the ingredient's current cost as the
    # best available migration-time cost basis.
    op.execute(
        """
        UPDATE inventory_movements AS im
        SET unit_cost = i.cost_per_unit
        FROM ingredients AS i
        WHERE i.id = im.ingredient_id
        """
    )

    # All existing inventory movements should now have a cost.
    op.alter_column(
        "inventory_movements",
        "unit_cost",
        existing_type=sa.Numeric(
            precision=10,
            scale=2,
        ),
        nullable=False,
    )

    # Inventory quantities use three decimal places so they match
    # recipe quantities and avoid unnecessary rounding.
    op.alter_column(
        "inventory_movements",
        "quantity",
        existing_type=sa.Numeric(
            precision=10,
            scale=2,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=3,
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "ingredients",
        "current_stock",
        existing_type=sa.Numeric(
            precision=10,
            scale=2,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=3,
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "ingredients",
        "minimum_stock",
        existing_type=sa.Numeric(
            precision=10,
            scale=2,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=3,
        ),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "ingredients",
        "minimum_stock",
        existing_type=sa.Numeric(
            precision=10,
            scale=3,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=2,
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "ingredients",
        "current_stock",
        existing_type=sa.Numeric(
            precision=10,
            scale=3,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=2,
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "inventory_movements",
        "quantity",
        existing_type=sa.Numeric(
            precision=10,
            scale=3,
        ),
        type_=sa.Numeric(
            precision=10,
            scale=2,
        ),
        existing_nullable=False,
    )

    op.drop_column(
        "inventory_movements",
        "unit_cost",
    )

