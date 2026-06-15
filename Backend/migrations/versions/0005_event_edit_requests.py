"""add event edit requests

Revision ID: 0005_event_edit_requests
Revises: 0004_update_ticket_status
Create Date: 2025-12-15 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_event_edit_requests"
down_revision: Union[str, None] = "0004_update_ticket_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_edit_requests",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("event_id", sa.String(length=50), nullable=False),
        sa.Column("requested_by_id", sa.String(length=50), nullable=False),
        sa.Column("reviewer_id", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status in ('pending','approved','rejected')",
            name="ck_event_edit_requests_status_valid",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_event_edit_requests_event_id"),
        "event_edit_requests",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_edit_requests_requested_by_id"),
        "event_edit_requests",
        ["requested_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_edit_requests_status"),
        "event_edit_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_edit_requests_status"), table_name="event_edit_requests")
    op.drop_index(op.f("ix_event_edit_requests_requested_by_id"), table_name="event_edit_requests")
    op.drop_index(op.f("ix_event_edit_requests_event_id"), table_name="event_edit_requests")
    op.drop_table("event_edit_requests")
