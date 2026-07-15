"""Initial migration — create papers table.

Revision ID: 001
Revises:
Create Date: 2026-07-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the ``papers`` table matching the Paper ORM model."""
    op.create_table(
        "papers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column(
            "doi",
            sa.String(255),
            nullable=True,
        ),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("pdf_path", sa.String(1000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doi", name="uq_papers_doi"),
    )

    # The id index is technically redundant with the PK index, but the model
    # explicitly declares ``index=True`` — keep in sync.
    op.create_index(op.f("ix_papers_id"), "papers", ["id"], unique=False)

    op.create_index(op.f("ix_papers_title"), "papers", ["title"], unique=False)

    # The model declares both ``unique=True`` and ``index=True`` on doi.
    # The UniqueConstraint above already creates a unique index in PostgreSQL,
    # but the explicit index is added to keep the schema consistent with the
    # ORM model definition.
    op.create_index(
        op.f("ix_papers_doi"), "papers", ["doi"], unique=False
    )


def downgrade() -> None:
    """Drop the ``papers`` table and all associated indexes."""
    op.drop_index(op.f("ix_papers_doi"), table_name="papers")
    op.drop_index(op.f("ix_papers_title"), table_name="papers")
    op.drop_index(op.f("ix_papers_id"), table_name="papers")
    op.drop_table("papers")
