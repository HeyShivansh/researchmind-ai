"""Create paper_chunks table.

Revision ID: 002
Revises: 001
Create Date: 2026-07-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the ``paper_chunks`` table matching the PaperChunk ORM model."""
    op.create_table(
        "paper_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "paper_id",
            sa.Uuid(),
            sa.ForeignKey("papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index on paper_id for fast lookups by paper.
    op.create_index(
        op.f("ix_paper_chunks_paper_id"),
        "paper_chunks",
        ["paper_id"],
        unique=False,
    )

    # Composite index on (paper_id, chunk_index) for ordered retrieval.
    op.create_index(
        op.f("ix_paper_chunks_paper_id_chunk_index"),
        "paper_chunks",
        ["paper_id", "chunk_index"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the ``paper_chunks`` table and all associated indexes."""
    op.drop_index(
        op.f("ix_paper_chunks_paper_id_chunk_index"),
        table_name="paper_chunks",
    )
    op.drop_index(
        op.f("ix_paper_chunks_paper_id"),
        table_name="paper_chunks",
    )
    op.drop_table("paper_chunks")
