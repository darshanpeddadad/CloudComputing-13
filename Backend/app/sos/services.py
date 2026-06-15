from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.sos.models import SOSAlert, SOSStatus
from app.sos.schemas import SOSAlertCreate, SOSAlertUpdate


class SOSService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(self, user_id: str, data: SOSAlertCreate) -> SOSAlert:
        alert = SOSAlert(
            event_id=data.event_id,
            user_id=user_id,
            latitude=data.latitude,
            longitude=data.longitude,
            message=data.message,
            status=SOSStatus.ACTIVE.value,
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        # eagerly load relationships for notification payload
        # specifically event and user
        # We can do a re-query or use refresh with options if supported, but re-query is safer for async
        return await self.get_alert_by_id(alert.id)

    async def get_alert_by_id(self, alert_id: str) -> Optional[SOSAlert]:
        stmt = (
            select(SOSAlert)
            .where(SOSAlert.id == alert_id)
            .options(selectinload(SOSAlert.event), selectinload(SOSAlert.user), selectinload(SOSAlert.resolver))
        )
        return await self.session.scalar(stmt)

    async def get_alerts_for_event(self, event_id: str, page: int = 1, page_size: int = 10) -> Tuple[List[SOSAlert], int]:
        offset = (page - 1) * page_size

        total_stmt = select(func.count(SOSAlert.id)).where(SOSAlert.event_id == event_id)
        total = await self.session.scalar(total_stmt)

        stmt = (
            select(SOSAlert)
            .where(SOSAlert.event_id == event_id)
            .order_by(SOSAlert.created_at.desc())
            .limit(page_size)
            .offset(offset)
            .options(
                selectinload(SOSAlert.event),
                selectinload(SOSAlert.user),
                selectinload(SOSAlert.resolver),
            )
        )
        result = await self.session.scalars(stmt)
        return list(result.all()), int(total or 0)

    async def get_active_alerts(self) -> List[SOSAlert]:
        stmt = (
            select(SOSAlert)
            .where(SOSAlert.status == SOSStatus.ACTIVE.value)
            .order_by(SOSAlert.created_at.desc())
            .options(selectinload(SOSAlert.event), selectinload(SOSAlert.user))
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_alerts_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        status: Optional[SOSStatus] = None,
    ) -> Tuple[List[SOSAlert], int]:
        offset = (page - 1) * page_size

        filters = []
        if status:
            filters.append(SOSAlert.status == status.value)

        count_stmt = select(func.count(SOSAlert.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = await self.session.scalar(count_stmt)

        stmt = (
            select(SOSAlert)
            .where(*filters)
            .order_by(SOSAlert.created_at.desc())
            .limit(page_size)
            .offset(offset)
            .options(selectinload(SOSAlert.event), selectinload(SOSAlert.user), selectinload(SOSAlert.resolver))
        )
        alerts = list((await self.session.scalars(stmt)).all())
        return alerts, int(total or 0)

    async def update_alert_status(self, alert_id: str, status: SOSStatus, resolver_id: Optional[str]) -> Optional[SOSAlert]:
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return None
        
        alert.status = status.value
        if status == SOSStatus.RESOLVED:
            alert.resolved_at = datetime.utcnow()
            alert.resolver_id = resolver_id
        
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
