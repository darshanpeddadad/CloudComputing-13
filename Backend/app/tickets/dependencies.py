from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.tickets.services.ticket_service import TicketService
from app.tickets.controllers.ticket_controller import TicketController
from app.tickets.controllers.ticket_type_controller import TicketTypeController
from app.tickets.repositories import TicketRepository
from app.rewards.dependencies import get_reward_service
from app.rewards.services import RewardService


async def get_ticket_service(session: AsyncSession = Depends(get_session)) -> TicketService:
    repo = TicketRepository(session)
    return TicketService(session, repo)


def get_ticket_controller(
    service: TicketService = Depends(get_ticket_service),
    reward_service: RewardService = Depends(get_reward_service),
) -> TicketController:
    return TicketController(service, reward_service)


def get_ticket_type_controller(service: TicketService = Depends(get_ticket_service)) -> TicketTypeController:
    return TicketTypeController(service)
