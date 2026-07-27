"""Add 2FA fields to users table

Revision ID: 0006_add_2fa_fields
Revises: 0005_event_edit_requests
Create Date: 2026-01-22 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_add_2fa_fields'
down_revision: Union[str, None] = '0005_event_edit_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('two_factor_secret', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('is_two_factor_enabled', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('backup_codes', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'backup_codes')
    op.drop_column('users', 'is_two_factor_enabled')
    op.drop_column('users', 'two_factor_secret')
