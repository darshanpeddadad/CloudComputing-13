"""
Reward System Dependencies

FastAPI dependency injection setup for reward system.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.rewards.repositories import RewardRepository
from app.rewards.services import (
    PointCalculator,
    BadgeService,
    LeaderboardService,
    RedemptionService,
    RewardService,
    StreakService,
)
from app.rewards.controllers import RewardController


async def get_reward_repository(
    session: AsyncSession = Depends(get_session),
) -> RewardRepository:
    """Get reward repository instance."""
    return RewardRepository(session)


def get_point_calculator() -> PointCalculator:
    """Get point calculator instance."""
    return PointCalculator()


async def get_badge_service(
    repository: RewardRepository = Depends(get_reward_repository),
) -> BadgeService:
    """Get badge service instance."""
    return BadgeService(repository)


async def get_leaderboard_service(
    repository: RewardRepository = Depends(get_reward_repository),
) -> LeaderboardService:
    """Get leaderboard service instance."""
    return LeaderboardService(repository)


async def get_redemption_service(
    repository: RewardRepository = Depends(get_reward_repository),
) -> RedemptionService:
    """Get redemption service instance."""
    return RedemptionService(repository)


async def get_streak_service(
    repository: RewardRepository = Depends(get_reward_repository),
) -> StreakService:
    """Get streak service instance."""
    return StreakService(repository)


async def get_reward_service(
    repository: RewardRepository = Depends(get_reward_repository),
    point_calculator: PointCalculator = Depends(get_point_calculator),
    badge_service: BadgeService = Depends(get_badge_service),
    streak_service: StreakService = Depends(get_streak_service),
) -> RewardService:
    """Get main reward service instance."""
    return RewardService(
        repository=repository,
        point_calculator=point_calculator,
        badge_service=badge_service,
        streak_service=streak_service,
    )


async def get_reward_controller(
    reward_service: RewardService = Depends(get_reward_service),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
    redemption_service: RedemptionService = Depends(get_redemption_service),
    streak_service: StreakService = Depends(get_streak_service),
) -> RewardController:
    """Get reward controller instance."""
    return RewardController(
        reward_service=reward_service,
        leaderboard_service=leaderboard_service,
        redemption_service=redemption_service,
        streak_service=streak_service,
    )
