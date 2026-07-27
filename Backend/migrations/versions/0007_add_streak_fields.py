"""Add streak fields to user_reward_profiles

Revision ID: 0007_add_streak_fields
Revises: 0006_add_2fa_fields
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_add_streak_fields'
down_revision: Union[str, None] = '0006_add_2fa_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add streak tracking columns to user_reward_profiles
    op.add_column(
        'user_reward_profiles',
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'user_reward_profiles',
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'user_reward_profiles',
        sa.Column('last_activity_week', sa.String(10), nullable=True)
    )
    op.add_column(
        'user_reward_profiles',
        sa.Column('streak_multiplier', sa.Float(), nullable=False, server_default='1.0')
    )


def downgrade() -> None:
    # Remove streak tracking columns
    op.drop_column('user_reward_profiles', 'streak_multiplier')
    op.drop_column('user_reward_profiles', 'last_activity_week')
    op.drop_column('user_reward_profiles', 'longest_streak')
    op.drop_column('user_reward_profiles', 'current_streak')
