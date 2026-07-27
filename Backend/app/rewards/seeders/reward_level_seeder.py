"""
Reward Levels Seeder

Seeds the database with default reward levels/badges.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rewards.models import RewardLevel
from app.rewards.rules.badge_rules import BADGE_THRESHOLDS


async def seed_reward_levels(session: AsyncSession) -> None:
    """
    Seed default reward levels into the database.
    
    This function is idempotent - it will only create levels that don't exist.
    """
    for badge in BADGE_THRESHOLDS:
        # Check if level already exists
        stmt = select(RewardLevel).where(RewardLevel.id == badge["id"])
        existing = await session.scalar(stmt)
        
        if existing:
            # Update existing level
            existing.name = badge["name"]
            existing.description = badge["description"]
            existing.min_points = badge["min_points"]
            existing.badge_color = badge["badge_color"]
            existing.priority = badge["priority"]
        else:
            # Create new level
            level = RewardLevel(
                id=badge["id"],
                name=badge["name"],
                description=badge["description"],
                min_points=badge["min_points"],
                badge_color=badge["badge_color"],
                priority=badge["priority"],
            )
            session.add(level)
    
    await session.commit()
    print(f"Seeded {len(BADGE_THRESHOLDS)} reward levels")
