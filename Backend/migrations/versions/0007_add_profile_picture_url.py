"""Add profile_picture_url to user_profiles table

Revision ID: 0007_add_profile_picture_url
Revises: 0006_add_2fa_fields
Create Date: 2026-01-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_add_profile_picture_url'
down_revision: Union[str, None] = '0006_add_2fa_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_profiles', sa.Column('profile_picture_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('user_profiles', 'profile_picture_url')