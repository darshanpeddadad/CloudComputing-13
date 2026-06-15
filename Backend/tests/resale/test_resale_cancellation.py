from datetime import datetime, timedelta
import asyncio

from fastapi.testclient import TestClient

from tests.auth.utils import detail_message
from tests.resale.test_resale_flow import (
    approve_event,
    create_event,
    create_ticket_type,
    ensure_categories,
    purchase_ticket,
    register_new_user,
)
from app.database import SessionLocal
from app.tickets.models import Ticket, TicketStatus


def _setup_active_listing(client: TestClient, seller, organizer):
    """Create an approved event, issue a ticket to the seller, and list it for resale."""
    ensure_categories()
    event_id = create_event(client, organizer)
    approve_event(client, event_id, organizer["headers"])
    ticket_type_id = create_ticket_type(client, event_id, organizer["headers"])
    ticket_id = purchase_ticket(client, event_id, ticket_type_id, seller["headers"])

    payload = {
        "ticket_id": ticket_id,
        "asking_price": 75.0,
        "currency": "USD",
        "allow_offers": False,
        "expires_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
    }
    list_resp = client.post("/api/resale/listings", json=payload, headers=seller["headers"])
    assert list_resp.status_code == 201, f"Listing creation failed: {list_resp.text}"
    return list_resp.json()


def _get_ticket(ticket_id: str) -> Ticket | None:
    async def _run():
        async with SessionLocal() as session:
            return await session.get(Ticket, ticket_id)

    return asyncio.run(_run())


def test_seller_can_cancel_active_listing(client: TestClient, auth_user, auth_admin):
    listing = _setup_active_listing(client, auth_user, auth_admin)

    cancel_resp = client.post(
        f"/api/resale/listings/{listing['id']}/cancel",
        headers=auth_user["headers"],
    )
    assert cancel_resp.status_code == 200
    data = cancel_resp.json()
    assert data["status"] == "cancelled"
    assert data["id"] == listing["id"]
    ticket = _get_ticket(listing["ticket_id"])
    assert ticket is not None
    assert ticket.status == TicketStatus.ISSUED.value

    # Cancelled listings should not appear in the active listings feed
    listings_resp = client.get("/api/resale/listings", headers=auth_user["headers"])
    assert listings_resp.status_code == 200
    active_listings = listings_resp.json()
    assert all(item["id"] != listing["id"] for item in active_listings)


def test_non_owner_cannot_cancel_listing(client: TestClient, auth_user, auth_admin):
    listing = _setup_active_listing(client, auth_user, auth_admin)
    attacker = register_new_user(client)

    response = client.post(
        f"/api/resale/listings/{listing['id']}/cancel",
        headers=attacker["headers"],
    )
    assert response.status_code == 403
    assert "not authorized" in detail_message(response) or "do not own" in detail_message(response)


def test_cannot_cancel_sold_listing(client: TestClient, auth_user, auth_admin):
    listing = _setup_active_listing(client, auth_user, auth_admin)
    buyer = register_new_user(client)

    purchase_resp = client.post(
        f"/api/resale/listings/{listing['id']}/purchase",
        headers=buyer["headers"],
    )
    assert purchase_resp.status_code == 200
    assert purchase_resp.json()["status"] == "sold"

    cancel_resp = client.post(
        f"/api/resale/listings/{listing['id']}/cancel",
        headers=auth_user["headers"],
    )
    assert cancel_resp.status_code == 400
    assert "cannot cancel" in detail_message(cancel_resp) or "status sold" in detail_message(cancel_resp)
