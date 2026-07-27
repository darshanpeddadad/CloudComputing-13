import asyncio
import uuid
from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.chat.models import ChatParticipant, ChatRoom, ChatRoomType
from app.database import SessionLocal
from app.events.models import EventStatus
from app.tickets.models import Ticket, TicketStatus
from Backend.tests.auth.utils import detail_message


def _fetch_ticket(ticket_id: str) -> Ticket | None:
    async def _run():
        async with SessionLocal() as session:
            return await session.get(Ticket, ticket_id)

    return asyncio.run(_run())


def _count_tickets() -> int:
    async def _run():
        async with SessionLocal() as session:
            total = await session.scalar(select(func.count(Ticket.id)))
            return int(total or 0)

    return asyncio.run(_run())


def _chat_members_for_event(event_id: str):
    async def _run():
        async with SessionLocal() as session:
            room_stmt = select(ChatRoom).where(
                ChatRoom.event_id == event_id,
                ChatRoom.room_type == ChatRoomType.EVENT_GROUP.value,
            )
            room = (await session.scalars(room_stmt)).first()
            if not room:
                return None, []
            participants = (await session.scalars(
                select(ChatParticipant).where(ChatParticipant.room_id == room.id)
            )).all()
            return room, participants

    return asyncio.run(_run())


def test_authenticated_user_can_purchase_ticket(
    client: TestClient,
    auth_user,
    approved_event_with_ticket_type,
):
    event_setup = approved_event_with_ticket_type()
    payload = {
        "event_id": event_setup["event"].id,
        "ticket_type_id": event_setup["ticket_type"].id,
    }

    response = client.post("/api/tickets/purchase", json=payload, headers=auth_user["headers"])

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"]
    data = body["data"]
    assert data["event_id"] == payload["event_id"]
    assert data["status"] == TicketStatus.ISSUED.value
    assert data["ticket_id"]

    ticket = _fetch_ticket(data["ticket_id"])
    assert ticket is not None
    assert ticket.owner_id == auth_user["user"]["id"]
    assert ticket.event_id == payload["event_id"]
    assert ticket.ticket_type_id == payload["ticket_type_id"]
    assert ticket.purchased_at is not None

    room, participants = _chat_members_for_event(payload["event_id"])
    assert room is not None
    assert any(p.user_id == auth_user["user"]["id"] for p in participants)


def test_anonymous_user_cannot_purchase_ticket(client: TestClient):
    payload = {"event_id": str(uuid.uuid4()), "ticket_type_id": str(uuid.uuid4())}

    response = client.post("/api/tickets/purchase", json=payload)

    assert response.status_code == 401
    assert "not authenticated" in detail_message(response)
    assert _count_tickets() == 0


def test_event_must_exist_for_purchase(client: TestClient, auth_user):
    payload = {"event_id": "missing-event", "ticket_type_id": "missing-ticket-type"}

    response = client.post("/api/tickets/purchase", json=payload, headers=auth_user["headers"])

    assert response.status_code == 400
    detail = detail_message(response)
    assert "event not found" in detail
    assert _count_tickets() == 0


def test_cannot_purchase_ticket_for_unapproved_event(
    client: TestClient,
    auth_user,
    approved_event_with_ticket_type,
):
    event_setup = approved_event_with_ticket_type(status=EventStatus.PENDING.value)
    payload = {
        "event_id": event_setup["event"].id,
        "ticket_type_id": event_setup["ticket_type"].id,
    }

    response = client.post("/api/tickets/purchase", json=payload, headers=auth_user["headers"])

    assert response.status_code == 400
    assert "not approved" in detail_message(response)
    assert _count_tickets() == 0


def test_cannot_purchase_ticket_for_ended_event(
    client: TestClient,
    auth_user,
    approved_event_with_ticket_type,
):
    past_date = date(2020, 1, 1)
    event_setup = approved_event_with_ticket_type(
        start_date=past_date,
        end_date=past_date,
        start_time=time(10, 0),
        end_time=time(12, 0),
    )
    payload = {
        "event_id": event_setup["event"].id,
        "ticket_type_id": event_setup["ticket_type"].id,
    }

    response = client.post("/api/tickets/purchase", json=payload, headers=auth_user["headers"])

    assert response.status_code == 400
    assert "ended" in detail_message(response)
    assert _count_tickets() == 0


def test_purchase_joins_event_group_chat(
    client: TestClient,
    auth_user,
    approved_event_with_ticket_type,
):
    event_setup = approved_event_with_ticket_type()
    payload = {
        "event_id": event_setup["event"].id,
        "ticket_type_id": event_setup["ticket_type"].id,
    }

    room_before, participants_before = _chat_members_for_event(payload["event_id"])
    assert room_before is None
    assert participants_before == []

    response = client.post("/api/tickets/purchase", json=payload, headers=auth_user["headers"])

    assert response.status_code == 200
    room_after, participants_after = _chat_members_for_event(payload["event_id"])
    assert room_after is not None
    assert any(p.user_id == auth_user["user"]["id"] for p in participants_after)
