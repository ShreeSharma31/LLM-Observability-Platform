"""create logs table

Revision ID: 0001_create_logs
Revises:
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("user", sa.String(), nullable=False),
        sa.Column("feature", sa.String(), nullable=False),
        sa.Column("environment", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_logs_id", "logs", ["id"])
    op.create_index("ix_logs_created_at", "logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_logs_created_at", table_name="logs")
    op.drop_index("ix_logs_id", table_name="logs")
    op.drop_table("logs")
