from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.rewards.schemas import (
    UserRewardProfileResponse,
    PointHistoryResponse,
    LeaderboardResponse,
    RedemptionPreviewRequest,
    RedemptionPreviewResponse,
    AllBadgesResponse,
    StreakInfoResponse,
    NextEventRecommendationsResponse,
)

if TYPE_CHECKING:
    from app.rewards.services import (
        RewardService,
        LeaderboardService,
        RedemptionService,
        StreakService,
    )
    from app.auth.models import User


DEFAULT_STREAK_INFO = StreakInfoResponse(
    current_streak=0,
    longest_streak=0,
    streak_multiplier=1.0,
    bonus_percentage=0,
    last_activity_week=None,
    streak_is_active=False,
    streak_at_risk=False,
    next_milestone=None,
    weeks_to_next_milestone=None,
)


class RewardController:

    def __init__(
        self,
        reward_service: "RewardService",
        leaderboard_service: "LeaderboardService",
        redemption_service: "RedemptionService",
        streak_service: Optional["StreakService"] = None,
    ):
        self._reward_service = reward_service
        self._leaderboard_service = leaderboard_service
        self._redemption_service = redemption_service
        self._streak_service = streak_service

   
    async def get_my_profile(
        self,
        current_user: "User",
    ) -> UserRewardProfileResponse:
        """Get current user's reward profile."""
        return await self._reward_service.get_or_create_user_profile(
            current_user.id
        )

    async def get_user_profile(
        self,
        user_id: str,
    ) -> Optional[UserRewardProfileResponse]:
        """Get a specific user's reward profile (public view)."""
        return await self._reward_service.get_user_profile(user_id)

    async def get_my_transactions(
        self,
        current_user: "User",
        page: int = 1,
        page_size: int = 20,
    ) -> PointHistoryResponse:
        """Get current user's point transaction history."""
        return await self._reward_service.get_point_history(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )


    async def get_leaderboard(
        self,
        period: str = "all_time",
        page: int = 1,
        page_size: int = 50,
    ) -> LeaderboardResponse:
        """Get leaderboard for specified period."""
        return await self._leaderboard_service.get_leaderboard(
            period=period,
            page=page,
            page_size=page_size,
        )

    async def get_my_rank(
        self,
        current_user: "User",
    ) -> dict:
        """Get current user's rank on the leaderboard."""
        rank = await self._leaderboard_service.get_user_rank(current_user.id)
        return {
            "user_id": current_user.id,
            "rank": rank,
            "message": "Not ranked yet" if rank is None else f"You are ranked #{rank}",
        }

    async def preview_redemption(
        self,
        current_user: "User",
        request: RedemptionPreviewRequest,
    ) -> RedemptionPreviewResponse:
        """Preview a point redemption without committing."""
        return await self._redemption_service.preview_redemption(
            user_id=current_user.id,
            points_to_redeem=request.points_to_redeem,
            event_id=request.event_id,
            ticket_price=request.ticket_price,
        )

    async def get_redemption_rate(self) -> dict:
        """Get current redemption rate configuration."""
        return self._redemption_service.get_redemption_rate()

    async def get_all_badges(self) -> AllBadgesResponse:
        """Get all available badges."""
        return await self._reward_service.get_all_badges()

    async def get_my_streak(
        self,
        current_user: "User",
    ) -> StreakInfoResponse:
        """Get current user's streak information."""
        if not self._streak_service:
            return DEFAULT_STREAK_INFO
        
        streak_info = await self._streak_service.get_user_streak_info(current_user.id)
        return StreakInfoResponse(**streak_info)

    async def get_streak_multipliers(self) -> dict:
        """Get all streak multiplier tiers."""
        from app.rewards.rules.streak_rules import STREAK_CONFIG
        
        multipliers = STREAK_CONFIG["multipliers"]
        tiers = []
        
        for weeks, multiplier in sorted(multipliers.items()):
            bonus_pct = int((multiplier - 1.0) * 100)
            tiers.append({
                "min_weeks": weeks,
                "multiplier": multiplier,
                "bonus_percentage": bonus_pct,
                "label": f"{weeks}+ weeks" if weeks > 0 else "No streak",
            })
        
        max_multiplier = max(multipliers.values())
        
        return {
            "tiers": tiers,
            "max_multiplier": max_multiplier,
            "max_bonus_percentage": int((max_multiplier - 1.0) * 100),
        }

    async def get_next_event_recommendations(
        self,
        current_user: "User",
        limit: int = 5,
    ) -> NextEventRecommendationsResponse:
        """Get personalized next-event ticket recommendations for the current user."""
        return await self._reward_service.get_next_event_recommendations(
            user_id=current_user.id,
            limit=limit,
        )
