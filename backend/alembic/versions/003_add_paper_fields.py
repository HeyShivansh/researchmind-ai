"""Add fields to papers table for frontend integration.

Adds filename, file_size, page_count, chunk_count, status, author,
and subject columns to the papers table to support the frontend
Paper type requirements.

Revision ID: 003
Revises: 002
Create Date: 2026-07-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to the papers table."""
    op.add_column(
        "papers",
        sa.Column("filename", sa.String(500), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("file_size", sa.Integer(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("page_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("chunk_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="processing",
        ),
    )
    op.add_column(
        "papers",
        sa.Column("author", sa.String(500), nullable=True),
    )
    op.add_column(
        "papers",
        sa.Column("subject", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    """Drop the added columns from the papers table."""
    op.drop_column("papers", "subject")
    op.drop_column("papers", "author")
    op.drop_column("papers", "status")
    op.drop_column("papers", "chunk_count")
    op.drop_column("papers", "page_count")
    op.drop_column("papers", "file_size")
    op.drop_column("papers", "filename")
