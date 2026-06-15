from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from app.rewards.schemas import LeaderboardEntry, LeaderboardResponse

if TYPE_CHECKING:
    from app.rewards.repositories import RewardRepository


class LeaderboardService:
    def __init__(self, repository: "RewardRepository"):
        self._repository = repository

    async def get_leaderboard(
        self,
        period: str = "all_time",
        page: int = 1,
        page_size: int = 50,
    ) -> LeaderboardResponse:

        if period not in ["all_time", "weekly", "monthly"]:
            period = "all_time"
        
        page = max(1, page)
        page_size = min(100, max(10, page_size))
        
        if period == "all_time":
            entries_data, total = await self._repository.get_leaderboard_all_time(
                page=page,
                page_size=page_size,
            )
        else:
            entries_data, total = await self._repository.get_leaderboard_periodic(
                period=period,
                page=page,
                page_size=page_size,
            )
        
        entries = [
            LeaderboardEntry(
                rank=entry["rank"],
                user_id=entry["user_id"],
                first_name=entry["first_name"],
                last_name=entry["last_name"],
                lifetime_points=entry["lifetime_points"],
                events_attended=entry["events_attended"],
                badge_name=entry["badge_name"],
                badge_color=entry["badge_color"],
            )
            for entry in entries_data
        ]
        
        return LeaderboardResponse(
            entries=entries,
            total_users=total,
            page=page,
            page_size=page_size,
            period=period,
        )

    async def get_user_rank(self, user_id: str) -> Optional[int]:

        return await self._repository.get_user_rank(user_id)
