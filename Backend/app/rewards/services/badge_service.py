from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from app.rewards.rules.badge_rules import (
    get_badge_for_points,
    get_next_badge,
    get_points_to_next_badge,
)

if TYPE_CHECKING:
    from app.rewards.models import RewardLevel, UserRewardProfile
    from app.rewards.repositories import RewardRepository


class BadgeService:
    def __init__(self, repository: "RewardRepository"):
        self._repository = repository

    async def evaluate_user_badge(
        self,
        profile: "UserRewardProfile",
    ) -> Tuple[bool, Optional["RewardLevel"]]:

        # Get the badge user should have based on points
        deserved_level = await self._repository.get_reward_level_for_points(
            profile.lifetime_points
        )
        
        current_level_id = profile.level_id
        new_level_id = deserved_level.id if deserved_level else None
        
        if current_level_id != new_level_id:
            return True, deserved_level
        
        return False, None

    async def get_next_badge_info(
        self,
        profile: "UserRewardProfile",
    ) -> Tuple[Optional["RewardLevel"], Optional[int]]:
       
        next_level = await self._repository.get_next_reward_level(
            profile.lifetime_points
        )
        
        if not next_level:
            return None, None
        
        points_needed = next_level.min_points - profile.lifetime_points
        return next_level, points_needed

    async def check_and_upgrade_badge(
        self,
        profile: "UserRewardProfile",
    ) -> Tuple[bool, Optional["RewardLevel"]]:
        
        badge_changed, new_badge = await self.evaluate_user_badge(profile)
        
        if badge_changed and new_badge:
            # profile update with new badge
            await self._repository.update_user_profile(
                profile,
                new_level_id=new_badge.id,
            )
            return True, new_badge
        
        return False, None
