"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2024-06-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("first_names", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("dob", sa.String(length=20), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=50), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.String(length=50), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "interests",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(length=50), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("interests")
    op.drop_table("user_roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")
