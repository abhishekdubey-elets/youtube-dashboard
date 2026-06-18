"""add speaker column to summaries

Revision ID: 0002_add_speaker
Revises: 0001_initial
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_speaker"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("summaries", sa.Column("speaker", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("summaries", "speaker")
