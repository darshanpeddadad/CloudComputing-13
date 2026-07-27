import pytest
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from app.database import SessionLocal
from app.tickets.models import Ticket, TicketStatus
from app.seeders.event_category_seed import seed_event_categories

# Helpers
def ensure_categories():
    async def _run():
        async with SessionLocal() as session:
            await seed_event_categories(session)
            await session.commit()
    asyncio.run(_run())

def create_event(client, organizer):
    headers = organizer["headers"]
    user_id = organizer["user"]["id"]
    
    # 0. Ensure Categories exist
    ensure_categories()

    # 1. Get Category
    cat_resp = client.get("/api/categories/", headers=headers)
    
    category_id = None
    if cat_resp.status_code == 200:
        data = cat_resp.json().get("data", [])
        if data:
            category_id = data[0]["id"]
            
    if not category_id:
        # Should not happen after ensure_categories, but just in case
        category_id = str(uuid.uuid4())

    start_dt = datetime.utcnow() + timedelta(days=10)
    end_dt = start_dt + timedelta(hours=2)
    
    # Construct Payload with corrected fields based on previous failures/schema
    # Note: validation error was "Category not found", hopefully fixed.
    # Also ensuring latitude/longitude are floats
    payload = {
        "title": "Test Resale Event",
        "description": "Event for resale testing",
        "location": "Test Venue",
        "latitude": 0.0,
        "longitude": 0.0,
        "start_date": start_dt.date().isoformat(),
        "end_date": end_dt.date().isoformat(),
        "start_time": start_dt.time().isoformat(),
        "end_time": end_dt.time().isoformat(),
        "category_id": category_id,
        "organizer_id": user_id,
        "max_attendees": 100,
        "sos_enabled": False,
        "image_urls": []
    }
    
    data = {
        "event_data": json.dumps(payload)
    }
    
    response = client.post("/api/events/", data=data, headers=headers)
    assert response.status_code == 201, f"Create Event Failed: {response.text}"
    return response.json()["data"]["id"]

def approve_event(client, event_id, admin_headers):
    response = client.post(f"/api/events/{event_id}/approve", headers=admin_headers)
    assert response.status_code == 200, f"Approve Event Failed: {response.text}"

def create_ticket_type(client, event_id, headers):
    start_dt = datetime.utcnow()
    end_dt = start_dt + timedelta(days=20)
    
    payload = {
        "name": "General Admission",
        "description": "Regular ticket",
        "price": 50.0,
        "currency": "USD",
        "capacity": 100,
        "max_per_user": 5,
        "resale_allowed": True,
        "sale_starts_at": start_dt.isoformat(),
        "sale_ends_at": end_dt.isoformat()
    }
    response = client.post(f"/api/events/{event_id}/ticket-types", json=payload, headers=headers)
    assert response.status_code == 201, f"Create Ticket Type Failed: {response.text}"
    return response.json()["data"]["id"]

def purchase_ticket(client, event_id, ticket_type_id, headers):
    payload = {
        "event_id": event_id,
        "ticket_type_id": ticket_type_id,
        "quantity": 1
    }
    purchase_response = client.post("/api/tickets/purchase", json=payload, headers=headers)
    assert purchase_response.status_code == 200, f"Purchase failed: {purchase_response.text}"
    return purchase_response.json()["data"]["ticket_id"]


    return purchase_response.json()["data"]["ticket_id"]


    return purchase_response.json()["data"]["ticket_id"]


from tests.auth.utils import registration_payload

def register_new_user(client):
    payload = registration_payload()
    email = payload["email"]
    password = payload["password"]
    
    # Register
    reg_resp = client.post("/api/auth/register", json=payload)
    assert reg_resp.status_code == 201, f"Register Failed: {reg_resp.text}"
    
    # Login
    login_resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200, f"Login Failed: {login_resp.text}"
    token = login_resp.json()["data"]["access_token"]
    
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user": login_resp.json()["data"]["user"]
    }

def _get_ticket(ticket_id: str) -> Ticket | None:
    """Fetch a ticket by ID for assertions."""
    async def _run():
        async with SessionLocal() as session:
            return await session.get(Ticket, ticket_id)

    return asyncio.run(_run())


class TestResaleFlow:
    
    def test_create_listing_success(self, client, auth_user, auth_admin):
        # 1. Organizer (auth_admin used) creates event
        event_id = create_event(client, auth_admin)
        
        # 1.1 Approve Event (Admin action)
        approve_event(client, event_id, auth_admin["headers"])
        
        # 2. Create Ticket Type
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        
        # 3. User purchases ticket
        # ensure auth_admin is different from auth_user if we wanted that, but here auth_user is owner.
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        # 4. User lists ticket for resale
        payload = {
            "ticket_id": ticket_id,
            "asking_price": 60.0,
            "currency": "USD",
            "notes": "Selling my ticket"
        }
        response = client.post("/api/resale/listings", json=payload, headers=auth_user["headers"])
        
        assert response.status_code == 201, f"Success in creating listings: {response.text}"
        data = response.json()
        assert data["ticket_id"] == ticket_id
        assert data["status"] == "active"
        assert data["asking_price"] == 60.0

    def test_listing_moves_ticket_to_listed_status(self, client, auth_user, auth_admin):
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])

        payload = {
            "ticket_id": ticket_id,
            "asking_price": 65.0,
            "currency": "USD",
        }
        response = client.post("/api/resale/listings", json=payload, headers=auth_user["headers"])

        assert response.status_code == 201, f"Failed to create listing: {response.text}"
        ticket = _get_ticket(ticket_id)
        assert ticket is not None
        assert ticket.status == TicketStatus.LISTED.value

    def test_create_listing_unauthenticated(self, client):
        payload = {"ticket_id": "some-id", "asking_price": 50.0}
        response = client.post("/api/resale/listings", json=payload)
        assert response.status_code == 401

    def test_create_listing_not_owner(self, client, auth_user, auth_admin):
        # User A (Admin/Owner) buys ticket
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_admin["headers"]) 
        
        # Register User B (Attacker)
        user_b = register_new_user(client)
        
        # User B tries to list Admin's ticket
        payload = {
            "ticket_id": ticket_id,
            "asking_price": 60.0
        }
        response = client.post("/api/resale/listings", json=payload, headers=user_b["headers"])
        assert response.status_code == 403 

    def test_get_listings_success(self, client, auth_user, auth_admin):
        # Setup listing
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 50.0
        }, headers=auth_user["headers"])
        
        # Get listings
        response = client.get("/api/resale/listings", headers=auth_user["headers"])
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["ticket_id"] == ticket_id for item in data)

    def test_get_listings_include_event_details(self, client, auth_user, auth_admin):
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])

        client.post(
            "/api/resale/listings",
            json={"ticket_id": ticket_id, "asking_price": 50.0},
            headers=auth_user["headers"],
        )

        response = client.get("/api/resale/listings", headers=auth_user["headers"])
        assert response.status_code == 200
        listings = response.json()
        listing = next((item for item in listings if item["ticket_id"] == ticket_id), None)
        assert listing is not None

        event = listing.get("event")
        assert event is not None, "Event details should be included in listing"
        assert event["id"] == event_id
        assert event["title"] == "Test Resale Event"
        assert event["organizer"]["id"] == auth_admin["user"]["id"]
        assert event["category"]["id"]
        assert "images" in event

    def test_purchase_listing_success(self, client, auth_user, auth_admin):
        # User A (auth_user) sells
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        # Create listing
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 50.0
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # User B (New User) purchases
        user_b = register_new_user(client)
        buy_resp = client.post(f"/api/resale/listings/{listing_id}/purchase", headers=user_b["headers"])
        assert buy_resp.status_code == 200
        assert buy_resp.json()["status"] == "sold"
        
    def test_purchase_listing_unauthenticated(self, client, auth_user, auth_admin):
         # User A sells
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 50.0
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # Anon tries to buy
        response = client.post(f"/api/resale/listings/{listing_id}/purchase")
        assert response.status_code == 401

    def test_purchase_own_listing_failure(self, client, auth_user, auth_admin):
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 50.0
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # User A tries to buy their own listing
        response = client.post(f"/api/resale/listings/{listing_id}/purchase", headers=auth_user["headers"])
        assert response.status_code == 400

    def test_make_offer_success(self, client, auth_user, auth_admin):
        # User A sells
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 100.0,
            "allow_offers": True
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # User B (New User) makes offer
        user_b = register_new_user(client)
        offer_payload = {"offered_price": 80.0, "message": "Can you do 80?"}
        response = client.post(f"/api/resale/listings/{listing_id}/offers", json=offer_payload, headers=user_b["headers"])
        assert response.status_code == 201
        assert response.json()["status"] == "pending"

    def test_accept_offer_success(self, client, auth_user, auth_admin):
         # User A sells
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 100.0,
            "allow_offers": True
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # User B makes offer
        user_b = register_new_user(client)
        offer_payload = {"offered_price": 80.0}
        offer_resp = client.post(f"/api/resale/listings/{listing_id}/offers", json=offer_payload, headers=user_b["headers"])
        offer_id = offer_resp.json()["id"]
        
        # User A accepts
        accept_resp = client.post(f"/api/resale/offers/{offer_id}/accept", headers=auth_user["headers"])
        assert accept_resp.status_code == 200
        assert accept_resp.json()["status"] == "accepted"

    def test_resale_updates_chat_participants(self, client, auth_user, auth_admin):
        # User A sells
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        # Original Owner (User A) should be in chat
        # Need to fetch room ID? Or list my rooms.
        # Assuming user A has one room
        # Checking /api/chat/rooms
        resp = client.get("/api/chat/rooms", headers=auth_user["headers"])
        assert resp.status_code == 200, f"Get rooms failed: {resp.text}"
        rooms_a = resp.json()["data"]
        # Filter for event group room?
        event_rooms_a = [r for r in rooms_a if r["event_id"] == event_id and r["room_type"] == "event_group"]
        assert len(event_rooms_a) == 1
        room_id = event_rooms_a[0]["id"]
        
        # List resale
        list_resp = client.post("/api/resale/listings", json={
            "ticket_id": ticket_id,
            "asking_price": 50.0
        }, headers=auth_user["headers"])
        listing_id = list_resp.json()["id"]
        
        # User B buys
        user_b = register_new_user(client)
        buy_resp = client.post(f"/api/resale/listings/{listing_id}/purchase", headers=user_b["headers"])
        assert buy_resp.status_code == 200
        
        # Verify User A is REMOVED from chat (or at least role changed? Requirement said removed)
        rooms_a_after = client.get("/api/chat/rooms", headers=auth_user["headers"]).json()["data"]
        event_rooms_a_after = [r for r in rooms_a_after if r["id"] == room_id]
        if event_rooms_a_after:
             assert len(event_rooms_a_after) == 0, "Original owner should be removed from chat"
        
        # Verify User B is ADDED to chat
        rooms_b = client.get("/api/chat/rooms", headers=user_b["headers"]).json()["data"]
        event_rooms_b = [r for r in rooms_b if r["id"] == room_id]
        assert len(event_rooms_b) == 1, "Buyer should be added to chat"

    def test_create_listing_generic_exception(self, client, auth_user, auth_admin):
        # 1. Setup valid ticket
        event_id = create_event(client, auth_admin)
        approve_event(client, event_id, auth_admin["headers"])
        ticket_type_id = create_ticket_type(client, event_id, auth_admin["headers"])
        ticket_id = purchase_ticket(client, event_id, ticket_type_id, auth_user["headers"])
        
        # 2. Mock service to raise generic Exception
        # We need to patch the controller's service or the service method itself
        from unittest.mock import patch
        
        # Patching ResaleService.create_listing to raise Exception
        with patch("app.resale.services.resale_service.ResaleService.create_listing") as mock_create:
            mock_create.side_effect = Exception("Unexpected database error")
            
            payload = {
                "ticket_id": ticket_id,
                "asking_price": 60.0,
                "currency": "USD"
            }
            response = client.post("/api/resale/listings", json=payload, headers=auth_user["headers"])
            
            assert response.status_code == 400
            assert "Listing failed: Unexpected database error" in response.json()["detail"]
