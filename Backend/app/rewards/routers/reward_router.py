from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.rewards.dependencies import get_reward_controller
from app.rewards.controllers import RewardController
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


def get_reward_router() -> APIRouter:
    """Create and return the reward system router."""
    
    router = APIRouter(prefix="/api/rewards", tags=["Rewards"])

    @router.get(
        "/profile",
        response_model=UserRewardProfileResponse,
        summary="Get my reward profile",
        description="Get the current user's reward profile including points, badge, and progress.",
    )
    async def get_my_profile(
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> UserRewardProfileResponse:
        return await controller.get_my_profile(current_user)

    @router.get(
        "/profile/{user_id}",
        response_model=UserRewardProfileResponse,
        summary="Get user reward profile",
        description="Get a specific user's public reward profile.",
    )
    async def get_user_profile(
        user_id: str,
        controller: RewardController = Depends(get_reward_controller),
    ) -> UserRewardProfileResponse:
        profile = await controller.get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User reward profile not found",
            )
        return profile


    @router.get(
        "/transactions",
        response_model=PointHistoryResponse,
        summary="Get my point transactions",
        description="Get the current user's point transaction history.",
    )
    async def get_my_transactions(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=10, le=100, description="Items per page"),
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> PointHistoryResponse:
        return await controller.get_my_transactions(
            current_user=current_user,
            page=page,
            page_size=page_size,
        )

    @router.get(
        "/leaderboard",
        response_model=LeaderboardResponse,
        summary="Get leaderboard",
        description="Get the reward leaderboard. Supports all_time, weekly, and monthly periods.",
    )
    async def get_leaderboard(
        period: str = Query("all_time", description="Period: all_time, weekly, monthly"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=10, le=100, description="Items per page"),
        controller: RewardController = Depends(get_reward_controller),
    ) -> LeaderboardResponse:
        return await controller.get_leaderboard(
            period=period,
            page=page,
            page_size=page_size,
        )

    @router.get(
        "/leaderboard/my-rank",
        summary="Get my rank",
        description="Get the current user's rank on the all-time leaderboard.",
    )
    async def get_my_rank(
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> dict:
        return await controller.get_my_rank(current_user)

    @router.post(
        "/redemption/preview",
        response_model=RedemptionPreviewResponse,
        summary="Preview redemption",
        description="Preview a point redemption without committing. Returns calculated discount.",
    )
    async def preview_redemption(
        request: RedemptionPreviewRequest,
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> RedemptionPreviewResponse:
        return await controller.preview_redemption(current_user, request)

    @router.get(
        "/redemption/rate",
        summary="Get redemption rate",
        description="Get the current point-to-currency redemption rate.",
    )
    async def get_redemption_rate(
        controller: RewardController = Depends(get_reward_controller),
    ) -> dict:
        return await controller.get_redemption_rate()

    @router.get(
        "/badges",
        response_model=AllBadgesResponse,
        summary="Get all badges",
        description="Get all available reward badges/levels with their thresholds.",
    )
    async def get_all_badges(
        controller: RewardController = Depends(get_reward_controller),
    ) -> AllBadgesResponse:
        return await controller.get_all_badges()

    @router.get(
        "/recommendations/next-events",
        response_model=NextEventRecommendationsResponse,
        summary="Get personalized next-event recommendations",
        description="Recommend upcoming events based on points and interests. If no interest-category match exists, interest is ignored and ranking falls back to price/time factors.",
    )
    async def get_next_event_recommendations(
        limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> NextEventRecommendationsResponse:
        return await controller.get_next_event_recommendations(
            current_user=current_user,
            limit=limit,
        )

    @router.get(
        "/streak",
        response_model=StreakInfoResponse,
        summary="Get my streak info",
        description="Get the current user's streak information including multiplier and milestones.",
    )
    async def get_my_streak(
        current_user: User = Depends(get_current_user),
        controller: RewardController = Depends(get_reward_controller),
    ) -> StreakInfoResponse:
        return await controller.get_my_streak(current_user)

    @router.get(
        "/streak/multipliers",
        summary="Get streak multiplier tiers",
        description="Get all streak multiplier tiers and their thresholds.",
    )
    async def get_streak_multipliers(
        controller: RewardController = Depends(get_reward_controller),
    ) -> dict:
        return await controller.get_streak_multipliers()

    return router
