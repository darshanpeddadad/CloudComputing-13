from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.tickets.models import Ticket


class TicketRepository:
    """Persistence operations for tickets."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_ticket_with_relations(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket with event and owner relationships eagerly loaded."""
        stmt = (
            select(Ticket)
            .options(selectinload(Ticket.event), selectinload(Ticket.owner))
            .where(Ticket.id == ticket_id)
        )
        result = await self._session.scalars(stmt)
        return result.first()
