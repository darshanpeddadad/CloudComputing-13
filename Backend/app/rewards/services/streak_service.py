from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

from app.rewards.rules.streak_rules import (
    get_streak_multiplier,
    get_next_streak_milestone,
    get_streak_bonus_percentage,
    is_milestone,
    STREAK_CONFIG,
)

if TYPE_CHECKING:
    from app.rewards.repositories import RewardRepository
    from app.rewards.models import UserRewardProfile


class StreakService:

    def __init__(self, repository: "RewardRepository"):
        self._repository = repository

    async def update_streak_on_activity(
        self,
        user_id: str,
        activity_date: Optional[datetime] = None,
    ) -> dict:
        if activity_date is None:
            activity_date = datetime.utcnow()
        
        profile = await self._repository.get_or_create_user_profile(user_id)
        current_week = self._get_iso_week(activity_date)
        
        if profile.last_activity_week == current_week:
            return {
                "streak_updated": False,
                "reason": "already_active_this_week",
                "current_streak": profile.current_streak,
                "longest_streak": profile.longest_streak,
                "multiplier": profile.streak_multiplier,
                "bonus_percentage": get_streak_bonus_percentage(profile.current_streak),
            }
        
        old_streak = profile.current_streak
        
        if profile.last_activity_week is None:
            new_streak = 1
            streak_status = "started"
        elif self._is_consecutive_week(profile.last_activity_week, current_week):
            new_streak = profile.current_streak + 1
            streak_status = "increased"
        elif self._is_within_grace_period(profile.last_activity_week, current_week):
            new_streak = profile.current_streak + 1
            streak_status = "increased_with_grace"
        else:
            new_streak = 1
            streak_status = "reset"
        
        new_longest = max(profile.longest_streak, new_streak)
        new_multiplier = get_streak_multiplier(new_streak)
        hit_milestone = is_milestone(new_streak) and new_streak > old_streak
        
        await self._repository.update_streak(
            profile=profile,
            current_streak=new_streak,
            longest_streak=new_longest,
            last_activity_week=current_week,
            streak_multiplier=new_multiplier,
        )
        
        next_milestone = get_next_streak_milestone(new_streak)
        
        return {
            "streak_updated": True,
            "streak_status": streak_status,
            "previous_streak": old_streak,
            "current_streak": new_streak,
            "longest_streak": new_longest,
            "multiplier": new_multiplier,
            "bonus_percentage": get_streak_bonus_percentage(new_streak),
            "hit_milestone": hit_milestone,
            "next_milestone": {
                "weeks": next_milestone[0],
                "multiplier": next_milestone[1],
                "bonus_percentage": int((next_milestone[1] - 1.0) * 100),
            } if next_milestone else None,
            "weeks_to_next_milestone": next_milestone[0] - new_streak if next_milestone else None,
        }

    async def get_user_streak_info(self, user_id: str) -> dict:
        profile = await self._repository.get_or_create_user_profile(user_id)
        
        current_week = self._get_iso_week(datetime.utcnow())
        streak_is_active = self._is_streak_still_active(
            profile.last_activity_week,
            current_week
        )
        
        display_streak = profile.current_streak if streak_is_active else 0
        display_multiplier = get_streak_multiplier(display_streak)
        
        next_milestone = get_next_streak_milestone(display_streak)
        
        return {
            "current_streak": display_streak,
            "longest_streak": profile.longest_streak,
            "streak_multiplier": display_multiplier,
            "bonus_percentage": get_streak_bonus_percentage(display_streak),
            "last_activity_week": profile.last_activity_week,
            "streak_is_active": streak_is_active,
            "streak_at_risk": self._is_streak_at_risk(profile.last_activity_week, current_week),
            "next_milestone": {
                "weeks": next_milestone[0],
                "multiplier": next_milestone[1],
                "bonus_percentage": int((next_milestone[1] - 1.0) * 100),
            } if next_milestone else None,
            "weeks_to_next_milestone": next_milestone[0] - display_streak if next_milestone else None,
        }

    def _get_iso_week(self, dt: datetime) -> str:
        return dt.strftime("%G-W%V")

    def _parse_iso_week(self, week_str: str) -> datetime:
        return datetime.strptime(week_str + '-1', "%G-W%V-%u")

    def _is_consecutive_week(self, last_week: str, current_week: str) -> bool:
        try:
            last_dt = self._parse_iso_week(last_week)
            current_dt = self._parse_iso_week(current_week)
            diff_days = (current_dt - last_dt).days
            return diff_days == 7
        except (ValueError, TypeError):
            return False

    def _is_within_grace_period(self, last_week: str, current_week: str) -> bool:
        grace_weeks = STREAK_CONFIG.get("grace_period_weeks", 0)
        if grace_weeks == 0:
            return False
        
        try:
            last_dt = self._parse_iso_week(last_week)
            current_dt = self._parse_iso_week(current_week)
            diff_days = (current_dt - last_dt).days
            max_gap_days = (1 + grace_weeks) * 7
            return 7 < diff_days <= max_gap_days
        except (ValueError, TypeError):
            return False

    def _is_streak_still_active(
        self,
        last_activity_week: Optional[str],
        current_week: str,
    ) -> bool:
        if last_activity_week is None:
            return False
        
        if last_activity_week == current_week:
            return True
        
        return (
            self._is_consecutive_week(last_activity_week, current_week) or
            self._is_within_grace_period(last_activity_week, current_week)
        )

    def _is_streak_at_risk(
        self,
        last_activity_week: Optional[str],
        current_week: str,
    ) -> bool:
        if last_activity_week is None:
            return False
        
        if last_activity_week == current_week:
            return False
        
        return self._is_consecutive_week(last_activity_week, current_week)
