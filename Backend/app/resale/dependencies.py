from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.resale.services.resale_service import ResaleService
from app.resale.controllers.resale_controller import ResaleController

async def get_resale_service(session: AsyncSession = Depends(get_session)) -> ResaleService:
    return ResaleService(session)

def get_resale_controller(service: ResaleService = Depends(get_resale_service)) -> ResaleController:
    return ResaleController(service)
