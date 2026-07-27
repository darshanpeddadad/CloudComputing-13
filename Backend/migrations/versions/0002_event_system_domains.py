"""
Add ticketing, rewards, offers, chat, and resale domains.

Revision ID: 0002_event_system_domains
Revises: 0001_initial
Create Date: 2025-11-18 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_event_system_domains"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Events domain
    op.create_table(
        "event_categories",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_event_categories_name", "event_categories", ["name"], unique=True)

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("sos_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("max_attendees", sa.Integer(), nullable=False),
        sa.Column(
            "organizer_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.String(length=50),
            sa.ForeignKey("event_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status in ('pending','approved','rejected')",
            name="ck_events_status_valid",
        ),
    )
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"])
    op.create_index("ix_events_category_id", "events", ["category_id"])

    op.create_table(
        "event_images",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_event_images_event_id", "event_images", ["event_id"])

    # Ticketing domain
    op.create_table(
        "ticket_types",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("max_per_user", sa.Integer(), nullable=True),
        sa.Column("resale_allowed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("sale_starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sale_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("event_id", "name", name="uq_ticket_types_event_name"),
    )
    op.create_index("ix_ticket_types_event_id", "ticket_types", ["event_id"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "ticket_type_id",
            sa.String(length=50),
            sa.ForeignKey("ticket_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="issued"),
        sa.Column("seat_label", sa.String(length=50), nullable=True),
        sa.Column("qr_code", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("original_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('issued','checked_in','transferred','refunded','cancelled')",
            name="ck_tickets_status_valid",
        ),
        sa.UniqueConstraint("qr_code", name="uq_tickets_qr_code"),
    )
    op.create_index("ix_tickets_ticket_type_id", "tickets", ["ticket_type_id"])
    op.create_index("ix_tickets_event_id", "tickets", ["event_id"])
    op.create_index("ix_tickets_owner_id", "tickets", ["owner_id"])
    op.create_index("ix_tickets_event_status", "tickets", ["event_id", "status"])

    op.create_table(
        "ticket_assignments",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.String(length=50),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("guest_name", sa.String(length=255), nullable=True),
        sa.Column("guest_email", sa.String(length=255), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("ticket_id", name="uq_ticket_assignments_ticket"),
    )

    op.create_table(
        "ticket_transactions",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.String(length=50),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "seller_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_ticket_transactions_ticket_id", "ticket_transactions", ["ticket_id"])
    op.create_index("ix_ticket_transactions_event_id", "ticket_transactions", ["event_id"])
    op.create_index("ix_ticket_transactions_buyer_id", "ticket_transactions", ["buyer_id"])
    op.create_index("ix_ticket_transactions_seller_id", "ticket_transactions", ["seller_id"])

    # Rewards domain
    op.create_table(
        "reward_levels",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("badge_color", sa.String(length=20), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_reward_profiles",
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "level_id",
            sa.String(length=50),
            sa.ForeignKey("reward_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("current_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_events_joined", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level_assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_reward_profiles_level_id", "user_reward_profiles", ["level_id"])

    op.create_table(
        "event_participations",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ticket_id",
            sa.String(length=50),
            sa.ForeignKey("tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="registered"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_participations_event_user"),
        sa.CheckConstraint(
            "status in ('registered','attended','no_show')",
            name="ck_event_participations_status_valid",
        ),
    )
    op.create_index("ix_event_participations_event_id", "event_participations", ["event_id"])
    op.create_index("ix_event_participations_user_id", "event_participations", ["user_id"])

    op.create_table(
        "user_reward_ledger",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "profile_user_id",
            sa.String(length=50),
            sa.ForeignKey("user_reward_profiles.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ticket_id",
            sa.String(length=50),
            sa.ForeignKey("tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("points_delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reward_ledger_user_id", "user_reward_ledger", ["user_id"])
    op.create_index("ix_reward_ledger_event_id", "user_reward_ledger", ["event_id"])

    # Event offers domain
    op.create_table(
        "event_offers",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "min_points",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "max_points",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "level_id",
            sa.String(length=50),
            sa.ForeignKey("reward_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("inventory", sa.Integer(), nullable=True),
        sa.Column("per_user_limit", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status in ('draft','active','expired','archived')",
            name="ck_event_offers_status_valid",
        ),
    )
    op.create_index("ix_event_offers_event_id", "event_offers", ["event_id"])
    op.create_index("ix_event_offers_status", "event_offers", ["status"])

    op.create_table(
        "event_offer_claims",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "offer_id",
            sa.String(length=50),
            sa.ForeignKey("event_offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="invited"),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("offer_id", "user_id", name="uq_event_offer_claims_offer_user"),
        sa.CheckConstraint(
            "status in ('invited','accepted','declined','redeemed','expired')",
            name="ck_event_offer_claims_status_valid",
        ),
    )
    op.create_index("ix_event_offer_claims_offer_id", "event_offer_claims", ["offer_id"])
    op.create_index("ix_event_offer_claims_user_id", "event_offer_claims", ["user_id"])

    # Chat domain
    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("room_type", sa.String(length=20), nullable=False, server_default="event_group"),
        sa.Column(
            "event_id",
            sa.String(length=50),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("direct_key", sa.String(length=120), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.UniqueConstraint("direct_key", name="uq_chat_rooms_direct_key"),
        sa.CheckConstraint(
            "room_type in ('event_group','direct')",
            name="ck_chat_rooms_type_valid",
        ),
    )
    op.create_index("ix_chat_rooms_event_id", "chat_rooms", ["event_id"])

    op.create_table(
        "chat_participants",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "room_id",
            sa.String(length=50),
            sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="participant"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notifications_muted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("room_id", "user_id", name="uq_chat_participants_room_user"),
        sa.CheckConstraint(
            "role in ('participant','moderator','owner')",
            name="ck_chat_participants_role_valid",
        ),
    )
    op.create_index("ix_chat_participants_room_id", "chat_participants", ["room_id"])
    op.create_index("ix_chat_participants_user_id", "chat_participants", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "room_id",
            sa.String(length=50),
            sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "parent_message_id",
            sa.String(length=50),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message_type", sa.String(length=20), nullable=False, server_default="text"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["room_id"])
    op.create_index("ix_chat_messages_sender_id", "chat_messages", ["sender_id"])

    op.create_table(
        "message_reads",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(length=50),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_reads_message_user"),
    )
    op.create_index("ix_message_reads_message_id", "message_reads", ["message_id"])
    op.create_index("ix_message_reads_user_id", "message_reads", ["user_id"])

    # Resale domain
    op.create_table(
        "ticket_resale_listings",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.String(length=50),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "seller_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("asking_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("allow_offers", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("auto_accept_price", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "buyer_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sale_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status in ('draft','active','reserved','sold','cancelled','expired')",
            name="ck_resale_listings_status_valid",
        ),
    )
    op.create_index("ix_ticket_resale_listings_ticket_id", "ticket_resale_listings", ["ticket_id"])
    op.create_index("ix_ticket_resale_listings_seller_id", "ticket_resale_listings", ["seller_id"])
    op.create_index("ix_ticket_resale_listings_buyer_id", "ticket_resale_listings", ["buyer_id"])

    op.create_table(
        "ticket_resale_offers",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column(
            "listing_id",
            sa.String(length=50),
            sa.ForeignKey("ticket_resale_listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "buyer_id",
            sa.String(length=50),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("offered_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('pending','accepted','declined','withdrawn','expired')",
            name="ck_resale_offers_status_valid",
        ),
    )
    op.create_index("ix_ticket_resale_offers_listing_id", "ticket_resale_offers", ["listing_id"])
    op.create_index("ix_ticket_resale_offers_buyer_id", "ticket_resale_offers", ["buyer_id"])


def downgrade() -> None:
    op.drop_index("ix_ticket_resale_offers_buyer_id", table_name="ticket_resale_offers")
    op.drop_index("ix_ticket_resale_offers_listing_id", table_name="ticket_resale_offers")
    op.drop_table("ticket_resale_offers")

    op.drop_index("ix_ticket_resale_listings_buyer_id", table_name="ticket_resale_listings")
    op.drop_index("ix_ticket_resale_listings_seller_id", table_name="ticket_resale_listings")
    op.drop_index("ix_ticket_resale_listings_ticket_id", table_name="ticket_resale_listings")
    op.drop_table("ticket_resale_listings")

    op.drop_index("ix_message_reads_user_id", table_name="message_reads")
    op.drop_index("ix_message_reads_message_id", table_name="message_reads")
    op.drop_table("message_reads")

    op.drop_index("ix_chat_messages_sender_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_room_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_participants_user_id", table_name="chat_participants")
    op.drop_index("ix_chat_participants_room_id", table_name="chat_participants")
    op.drop_table("chat_participants")

    op.drop_index("ix_chat_rooms_event_id", table_name="chat_rooms")
    op.drop_table("chat_rooms")

    op.drop_index("ix_event_offer_claims_user_id", table_name="event_offer_claims")
    op.drop_index("ix_event_offer_claims_offer_id", table_name="event_offer_claims")
    op.drop_table("event_offer_claims")

    op.drop_index("ix_event_offers_status", table_name="event_offers")
    op.drop_index("ix_event_offers_event_id", table_name="event_offers")
    op.drop_table("event_offers")

    op.drop_index("ix_reward_ledger_event_id", table_name="user_reward_ledger")
    op.drop_index("ix_reward_ledger_user_id", table_name="user_reward_ledger")
    op.drop_table("user_reward_ledger")

    op.drop_index("ix_event_participations_user_id", table_name="event_participations")
    op.drop_index("ix_event_participations_event_id", table_name="event_participations")
    op.drop_table("event_participations")

    op.drop_index("ix_user_reward_profiles_level_id", table_name="user_reward_profiles")
    op.drop_table("user_reward_profiles")

    op.drop_table("reward_levels")

    op.drop_index("ix_ticket_transactions_seller_id", table_name="ticket_transactions")
    op.drop_index("ix_ticket_transactions_buyer_id", table_name="ticket_transactions")
    op.drop_index("ix_ticket_transactions_event_id", table_name="ticket_transactions")
    op.drop_index("ix_ticket_transactions_ticket_id", table_name="ticket_transactions")
    op.drop_table("ticket_transactions")

    op.drop_table("ticket_assignments")

    op.drop_index("ix_tickets_event_status", table_name="tickets")
    op.drop_index("ix_tickets_owner_id", table_name="tickets")
    op.drop_index("ix_tickets_event_id", table_name="tickets")
    op.drop_index("ix_tickets_ticket_type_id", table_name="tickets")
    op.drop_table("tickets")

    op.drop_index("ix_ticket_types_event_id", table_name="ticket_types")
    op.drop_table("ticket_types")

    op.drop_index("ix_event_images_event_id", table_name="event_images")
    op.drop_table("event_images")

    op.drop_index("ix_events_category_id", table_name="events")
    op.drop_index("ix_events_organizer_id", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_event_categories_name", table_name="event_categories")
    op.drop_table("event_categories")
