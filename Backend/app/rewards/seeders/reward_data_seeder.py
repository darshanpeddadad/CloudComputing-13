
from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.events.models import Event
from app.rewards.models import (
    EventParticipation,
    ParticipationStatus,
    RewardLevel,
    UserRewardLedger,
    UserRewardProfile,
)


# Seed configuration for different user profiles
USER_REWARD_PROFILES = [
    (6500, 45, True),   # Platinum user
    (4200, 30, True),   # Gold user
    (3100, 22, False),  # Gold user (no redemptions)
    (1800, 12, True),   # Silver user
    (1600, 11, False),  # Silver user
    (800, 6, True),     # Bronze user
    (550, 4, False),    # Bronze user
    (300, 2, False),    # No badge yet
    (100, 1, False),    # New user
    (50, 1, False),     # Very new user
]

# Point reasons for ledger entries
EARN_REASONS = [
    ("event_attendance", "Points earned for attending event"),
    ("event_attendance", "Points earned for event check-in"),
    ("bonus_points", "Early bird bonus points"),
    ("bonus_points", "Weekend event bonus"),
]

REDEEM_REASONS = [
    ("point_redemption", "Redeemed points for event discount"),
    ("point_redemption", "Points redeemed for ticket purchase"),
]


def _generate_ledger_id() -> str:
    """Generate a unique ledger entry ID."""
    return f"ledger_{uuid.uuid4().hex[:12]}"


def _generate_participation_id() -> str:
    """Generate a unique participation ID."""
    return f"part_{uuid.uuid4().hex[:12]}"


def _get_level_for_points(levels: List[RewardLevel], points: int) -> RewardLevel | None:
    """Get the appropriate reward level for given points."""
    qualifying = [l for l in levels if points >= l.min_points]
    if not qualifying:
        return None
    return max(qualifying, key=lambda l: l.min_points)


async def seed_reward_data(session: AsyncSession) -> Tuple[int, int, int]:
    """
    Seed reward data for existing users.
    
    Returns tuple of (profiles_created, ledger_entries_created, participations_created)
    """
    # Check if reward data already exists
    existing_profile = await session.scalar(select(UserRewardProfile.user_id).limit(1))
    if existing_profile:
        print("Reward data already exists, skipping reward data seeding")
        return (0, 0, 0)
    
    # Get seed users (created by event_user_seed)
    stmt = select(User).where(User.email.like("event-user-%@seed.fulda"))
    users = list(await session.scalars(stmt))
    
    if not users:
        print("No seed users found for reward seeding")
        return (0, 0, 0)
    
    # Get reward levels
    levels = list(await session.scalars(select(RewardLevel)))
    if not levels:
        print("No reward levels found, run seed_reward_levels first")
        return (0, 0, 0)
    
    # Get approved events for participation records
    stmt = select(Event).where(Event.status == "approved").limit(50)
    events = list(await session.scalars(stmt))
    
    profiles_created = 0
    ledger_entries_created = 0
    participations_created = 0
    
    # Create profiles and history for each user
    for i, user in enumerate(users):
        if i >= len(USER_REWARD_PROFILES):
            break
        
        target_lifetime, events_count, has_redemptions = USER_REWARD_PROFILES[i]
        
        # Calculate current points (lifetime minus any redemptions)
        redemption_amount = 0
        if has_redemptions:
            redemption_amount = random.randint(100, min(500, target_lifetime // 3))
        
        current_points = target_lifetime - redemption_amount
        
        # Get appropriate level
        level = _get_level_for_points(levels, target_lifetime)
        
        # Create user reward profile
        profile = UserRewardProfile(
            user_id=user.id,
            level_id=level.id if level else None,
            current_points=current_points,
            lifetime_points=target_lifetime,
            total_events_joined=events_count,
            level_assigned_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if level else None,
            updated_at=datetime.utcnow(),
        )
        session.add(profile)
        profiles_created += 1
        
        # Generate ledger entries (point history)
        # We'll create entries that sum up to the target lifetime points
        remaining_points = target_lifetime
        entry_date = datetime.utcnow() - timedelta(days=180)  # Start 6 months ago
        
        # Create earning entries
        entries_to_create = min(events_count + random.randint(0, 3), 20)
        points_per_entry = remaining_points // entries_to_create if entries_to_create > 0 else 0
        
        for j in range(entries_to_create):
            # Vary the points a bit
            if j == entries_to_create - 1:
                points = remaining_points  # Last entry gets remaining
            else:
                variance = random.randint(-20, 20)
                points = max(10, points_per_entry + variance)
                remaining_points -= points
            
            reason, description = random.choice(EARN_REASONS)
            
            # Pick an event if available
            event_id = None
            if events and j < len(events):
                event_id = events[j % len(events)].id
            
            entry = UserRewardLedger(
                id=_generate_ledger_id(),
                user_id=user.id,
                profile_user_id=user.id,
                event_id=event_id,
                ticket_id=None,
                points_delta=points,
                reason=reason,
                description=f"{description}: +{points} points",
                metadata_json={"source": "seeder", "event_index": j},
                created_at=entry_date,
            )
            session.add(entry)
            ledger_entries_created += 1
            
            # Create participation record if event exists
            if event_id:
                # Check if participation already exists
                existing_part = await session.scalar(
                    select(EventParticipation).where(
                        EventParticipation.event_id == event_id,
                        EventParticipation.user_id == user.id,
                    )
                )
                if not existing_part:
                    participation = EventParticipation(
                        id=_generate_participation_id(),
                        event_id=event_id,
                        user_id=user.id,
                        ticket_id=None,
                        status=ParticipationStatus.ATTENDED,
                        checked_in_at=entry_date,
                        registered_at=entry_date - timedelta(days=random.randint(1, 7)),
                    )
                    session.add(participation)
                    participations_created += 1
            
            # Advance date for next entry
            entry_date += timedelta(days=random.randint(3, 14))
        
        # Create redemption entries if applicable
        if has_redemptions and redemption_amount > 0:
            reason, description = random.choice(REDEEM_REASONS)
            entry = UserRewardLedger(
                id=_generate_ledger_id(),
                user_id=user.id,
                profile_user_id=user.id,
                event_id=None,
                ticket_id=None,
                points_delta=-redemption_amount,  # Negative for redemption
                reason=reason,
                description=f"{description}: -{redemption_amount} points",
                metadata_json={
                    "source": "seeder",
                    "redemption_type": "discount",
                    "discount_amount": redemption_amount / 100,  # €0.01 per point
                },
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
            )
            session.add(entry)
            ledger_entries_created += 1
    
    await session.commit()
    
    print(f"Seeded reward data: {profiles_created} profiles, {ledger_entries_created} ledger entries, {participations_created} participations")
    return (profiles_created, ledger_entries_created, participations_created)
