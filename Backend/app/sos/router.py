from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.user import User
from app.auth.utils.auth_checks import is_admin
from app.auth.dependencies import get_current_user
from app.database import get_session as get_db
from app.events.models.event import Event
from app.sos.models import SOSStatus
from app.sos.schemas import SOSAlertCreate, SOSAlertResponse, SOSAlertUpdate, SOSAlertListResponse
from app.sos.services import SOSService
from app.sos.socket_events import notify_admins


def get_sos_router(socket_server) -> APIRouter:
    router = APIRouter(prefix="/api/sos", tags=["SOS"])

    @router.post("/", response_model=SOSAlertResponse, status_code=status.HTTP_201_CREATED)
    async def trigger_sos(
        data: SOSAlertCreate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ):
        """
        Trigger an SOS alert for an event.
        Requires active user.
        """
        service = SOSService(session)
        # Verify event exists (optional, FK constraint will fail but nice to have)
        # For now, trust the FK constraint or service logic.
        
        alert = await service.create_alert(current_user.id, data)
        
        # Notify admins via Socket.IO
        await notify_admins(socket_server, alert)
        
        return alert
    
    @router.get("/", response_model=SOSAlertListResponse)
    async def list_all_alerts(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ):
        """
        List all SOS alerts (latest first) with pagination.

        Admin-only endpoint. Each alert now returns the triggering user,
        the related event, and resolver (if any) alongside the base SOS data.
        """
        if not is_admin(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        service = SOSService(session)
        alerts, total = await service.get_alerts_paginated(page=page, page_size=page_size)
        items = [SOSAlertResponse.model_validate(alert).model_dump() for alert in alerts]
        total_pages = (total + page_size - 1) // page_size
        return SOSAlertListResponse(
            items=items,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        )

    @router.get("/event/{event_id}", response_model=SOSAlertListResponse)
    async def list_event_alerts(
        event_id: str,
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=50),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ):
        """
        List SOS alerts for a specific event.
        Only accessible by Admins or Event Organizers.
        Returns full SOS details plus user, event, and resolver info.
        """
        service = SOSService(session)
        
        # Check permissions
        if not is_admin(current_user):
            event = await service.session.get(Event, event_id)
            if not event or event.organizer_id != current_user.id:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view SOS alerts for this event"
                )
        
        alerts, total = await service.get_alerts_for_event(event_id, page=page, page_size=page_size)
        items = [SOSAlertResponse.model_validate(alert).model_dump() for alert in alerts]
        total_pages = (total + page_size - 1) // page_size
        return SOSAlertListResponse(
            items=items,
            pagination={
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        )

    @router.patch("/{alert_id}", response_model=SOSAlertResponse)
    async def update_alert_status(
        alert_id: str,
        data: SOSAlertUpdate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ):
        """
        Update alert status (e.g., resolve it).
        Only accessible by Admins or Event Organizers.
        """
        service = SOSService(session)
        alert = await service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Check permissions
        if not is_admin(current_user):
            if alert.event.organizer_id != current_user.id:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this alert"
                )

        updated_alert = await service.update_alert_status(alert_id, data.status, current_user.id)
        
        # Optionally notify update? 
        # For MVP, just triggering.
        
        return updated_alert

    return router
