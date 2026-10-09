"""promo codes (PIZZA-91)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-05 09:41:27
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promo_codes",
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("discount_percent", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("times_used", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "discount_percent BETWEEN 1 AND 50", name="ck_promo_codes_discount_percent"
        ),
    )
    op.add_column(
        "orders",
        sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "orders",
        sa.Column("promo_code", sa.String(32), sa.ForeignKey("promo_codes.code"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "promo_code")
    op.drop_column("orders", "discount_amount")
    op.drop_table("promo_codes")
