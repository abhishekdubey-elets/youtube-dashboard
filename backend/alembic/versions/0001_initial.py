"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-17

Creates users, videos, transcripts, summaries and exports tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

# Each enum is referenced by exactly one table, so create_table()/drop_table()
# manage the CREATE TYPE / DROP TYPE lifecycle automatically (the standard
# Alembic pattern). No explicit .create()/.drop() calls — those would duplicate.
processing_status = sa.Enum(
    "queued",
    "downloading",
    "extracting",
    "transcribing",
    "summarizing",
    "exporting",
    "completed",
    "failed",
    "cancelled",
    name="processing_status",
)
user_role = sa.Enum("admin", "editor", "viewer", name="user_role")
export_status = sa.Enum("success", "failed", name="export_status")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", user_role, nullable=False, server_default="admin"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("youtube_video_id", sa.String(32), nullable=False),
        sa.Column("video_title", sa.String(512), nullable=False, server_default=""),
        sa.Column("channel_name", sa.String(255)),
        sa.Column("video_url", sa.String(512), nullable=False),
        sa.Column("playlist_name", sa.String(512)),
        sa.Column("upload_date", sa.String(32)),
        sa.Column("duration", sa.Integer()),
        sa.Column("thumbnail", sa.String(512)),
        sa.Column("status", processing_status, nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("youtube_video_id", name="uq_videos_youtube_id"),
    )
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"])
    op.create_index("ix_videos_status", "videos", ["status"])

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("full_transcript", sa.Text(), server_default=""),
        sa.Column("language", sa.String(16)),
        sa.Column("word_count", sa.Integer(), server_default="0"),
        sa.Column("processing_time", sa.Float()),
        sa.Column("provider", sa.String(32)),
        sa.Column("segments", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("video_id", name="uq_transcripts_video_id"),
    )
    op.create_index("ix_transcripts_video_id", "transcripts", ["video_id"])

    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("key_points", postgresql.JSONB()),
        sa.Column("quotes", postgresql.JSONB()),
        sa.Column("keywords", postgresql.JSONB()),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("topics", postgresql.JSONB()),
        sa.Column("action_items", postgresql.JSONB()),
        sa.Column("key_insights", postgresql.JSONB()),
        sa.Column("sentiment", sa.String(32)),
        sa.Column("sentiment_detail", postgresql.JSONB()),
        sa.Column("model", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("video_id", name="uq_summaries_video_id"),
    )
    op.create_index("ix_summaries_video_id", "summaries", ["video_id"])

    op.create_table(
        "exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("sheet_name", sa.String(255)),
        sa.Column("spreadsheet_id", sa.String(128)),
        sa.Column("status", export_status, nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text()),
        sa.Column("exported_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_exports_video_id", "exports", ["video_id"])


def downgrade() -> None:
    # drop_table() auto-drops each table's associated enum type.
    op.drop_table("exports")
    op.drop_table("summaries")
    op.drop_table("transcripts")
    op.drop_table("videos")
    op.drop_table("users")
