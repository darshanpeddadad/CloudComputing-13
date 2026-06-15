"""update ticket check constraint

Revision ID: 0004_update_ticket_status
Revises: 5b356b6b2de6
Create Date: 2025-12-11 11:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_update_ticket_status'
down_revision: Union[str, None] = '5b356b6b2de6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing constraint
    # Note: On SQLite, dropping constraints via name might vary or require batch mode. 
    # Alembic handles this somewhat, but explicit logic helps.
    try:
        op.drop_constraint('ck_tickets_status_valid', 'tickets', type_='check')
    except Exception:
        # Fallback/Ignore if not found or on strict backends
        pass

    # 2. Add new constraint with 'listed' included
    op.create_check_constraint(
        'ck_tickets_status_valid',
        'tickets',
        "status in ('issued','checked_in','transferred','refunded','cancelled','listed')"
    )


def downgrade() -> None:
    # Revert to original list
    try:
        op.drop_constraint('ck_tickets_status_valid', 'tickets', type_='check')
    except Exception:
        pass

    op.create_check_constraint(
        'ck_tickets_status_valid',
        'tickets',
        "status in ('issued','checked_in','transferred','refunded','cancelled')"
    )
