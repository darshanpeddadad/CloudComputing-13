from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.rewards.models import (
    RewardLevel,
    UserRewardProfile,
    UserRewardLedger,
    EventParticipation,
    ParticipationStatus,
)
from app.auth.models import User
from app.events.models import Event
from app.tickets.models import Ticket


class RewardRepository:
    """Repository for reward-related database operations."""

    def __init__(self, session: AsyncSession):
        self._session = session


    async def get_all_reward_levels(self) -> List[RewardLevel]:
        """Get all reward levels ordered by priority."""
        stmt = select(RewardLevel).order_by(RewardLevel.priority.asc())
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_reward_level_by_id(self, level_id: str) -> Optional[RewardLevel]:
        """Get a reward level by ID."""
        return await self._session.get(RewardLevel, level_id)

    async def get_reward_level_for_points(self, total_points: int) -> Optional[RewardLevel]:
        """Get the highest reward level the user qualifies for based on points."""
        stmt = (
            select(RewardLevel)
            .where(RewardLevel.min_points <= total_points)
            .order_by(RewardLevel.min_points.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def get_next_reward_level(self, total_points: int) -> Optional[RewardLevel]:
        """Get the next reward level the user can achieve."""
        stmt = (
            select(RewardLevel)
            .where(RewardLevel.min_points > total_points)
            .order_by(RewardLevel.min_points.asc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def create_reward_level(
        self,
        level_id: str,
        name: str,
        min_points: int,
        description: Optional[str] = None,
        badge_color: Optional[str] = None,
        priority: int = 0,
    ) -> RewardLevel:
        """Create a new reward level."""
        level = RewardLevel(
            id=level_id,
            name=name,
            description=description,
            min_points=min_points,
            badge_color=badge_color,
            priority=priority,
        )
        self._session.add(level)
        await self._session.flush()
        return level

    async def get_user_profile(self, user_id: str) -> Optional[UserRewardProfile]:
        """Get user's reward profile with level loaded."""
        stmt = (
            select(UserRewardProfile)
            .options(selectinload(UserRewardProfile.level))
            .where(UserRewardProfile.user_id == user_id)
        )
        return await self._session.scalar(stmt)

    async def get_or_create_user_profile(self, user_id: str) -> UserRewardProfile:
        """Get user's reward profile or create if not exists."""
        profile = await self.get_user_profile(user_id)
        if profile:
            return profile

        profile = UserRewardProfile(
            user_id=user_id,
            level_id=None,
            current_points=0,
            lifetime_points=0,
            total_events_joined=0,
            updated_at=datetime.utcnow(),
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def update_user_profile(
        self,
        profile: UserRewardProfile,
        points_delta: int = 0,
        increment_events: bool = False,
        new_level_id: Optional[str] = None,
    ) -> UserRewardProfile:
        """Update user's reward profile with point/event changes."""
        if points_delta > 0:
            profile.current_points += points_delta
            profile.lifetime_points += points_delta
        elif points_delta < 0:
            # Deduction
            profile.current_points = max(0, profile.current_points + points_delta)

        if increment_events:
            profile.total_events_joined += 1

        if new_level_id is not None and new_level_id != profile.level_id:
            profile.level_id = new_level_id
            profile.level_assigned_at = datetime.utcnow()

        profile.updated_at = datetime.utcnow()
        await self._session.flush()
        return profile

    async def update_streak(
        self,
        profile: UserRewardProfile,
        current_streak: int,
        longest_streak: int,
        last_activity_week: str,
        streak_multiplier: float,
    ) -> UserRewardProfile:
        """Update user's streak information."""
        profile.current_streak = current_streak
        profile.longest_streak = longest_streak
        profile.last_activity_week = last_activity_week
        profile.streak_multiplier = streak_multiplier
        profile.updated_at = datetime.utcnow()
        await self._session.flush()
        return profile


    async def create_ledger_entry(
        self,
        user_id: str,
        points_delta: int,
        reason: str,
        description: Optional[str] = None,
        event_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UserRewardLedger:
        """Create a point transaction ledger entry."""
        entry = UserRewardLedger(
            id=str(uuid.uuid4()),
            user_id=user_id,
            profile_user_id=user_id,
            event_id=event_id,
            ticket_id=ticket_id,
            points_delta=points_delta,
            reason=reason,
            description=description,
            metadata_json=metadata,
            created_at=datetime.utcnow(),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_user_transactions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[UserRewardLedger], int]:
        """Get paginated transaction history for a user."""
        # Total Count
        count_stmt = (
            select(func.count())
            .select_from(UserRewardLedger)
            .where(UserRewardLedger.user_id == user_id)
        )
        total = await self._session.scalar(count_stmt) or 0

        #Pagination of Results
        offset = (page - 1) * page_size
        stmt = (
            select(UserRewardLedger)
            .where(UserRewardLedger.user_id == user_id)
            .order_by(UserRewardLedger.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._session.scalars(stmt)
        return list(result.all()), total

    async def check_points_already_awarded(
        self,
        user_id: str,
        event_id: str,
        reason: str = "event_attendance",
    ) -> bool:
        """Check if points were already awarded for this event"""
        stmt = (
            select(func.count())
            .select_from(UserRewardLedger)
            .where(
                and_(
                    UserRewardLedger.user_id == user_id,
                    UserRewardLedger.event_id == event_id,
                    UserRewardLedger.reason == reason,
                    UserRewardLedger.points_delta > 0,
                )
            )
        )
        count = await self._session.scalar(stmt) or 0
        return count > 0

    async def get_participation(
        self,
        user_id: str,
        event_id: str,
    ) -> Optional[EventParticipation]:

        stmt = (
            select(EventParticipation)
            .where(
                and_(
                    EventParticipation.user_id == user_id,
                    EventParticipation.event_id == event_id,
                )
            )
        )
        return await self._session.scalar(stmt)

    async def create_participation(
        self,
        user_id: str,
        event_id: str,
        ticket_id: Optional[str] = None,
        status: str = ParticipationStatus.REGISTERED.value,
    ) -> EventParticipation:

        participation = EventParticipation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_id=event_id,
            ticket_id=ticket_id,
            status=status,
            registered_at=datetime.utcnow(),
        )
        self._session.add(participation)
        await self._session.flush()
        return participation

    async def update_participation_status(
        self,
        participation: EventParticipation,
        status: str,
    ) -> EventParticipation:

        participation.status = status
        if status == ParticipationStatus.ATTENDED.value:
            participation.checked_in_at = datetime.utcnow()
        await self._session.flush()
        return participation

    async def mark_participation_completed(
        self,
        participation: EventParticipation,
    ) -> EventParticipation:
        participation.completed_at = datetime.utcnow()
        await self._session.flush()
        return participation

    async def get_leaderboard_all_time(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[dict], int]:

        count_stmt = select(func.count()).select_from(UserRewardProfile)
        total = await self._session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size

        stmt = (
            select(
                UserRewardProfile.user_id,
                UserRewardProfile.lifetime_points,
                UserRewardProfile.total_events_joined,
                User.first_names,
                User.last_name,
                RewardLevel.name.label("badge_name"),
                RewardLevel.badge_color,
            )
            .join(User, UserRewardProfile.user_id == User.id)
            .outerjoin(RewardLevel, UserRewardProfile.level_id == RewardLevel.id)
            .where(UserRewardProfile.lifetime_points > 0)
            .order_by(UserRewardProfile.lifetime_points.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        entries = []
        for idx, row in enumerate(rows):
            entries.append({
                "rank": offset + idx + 1,
                "user_id": row.user_id,
                "first_name": row.first_names,
                "last_name": row.last_name,
                "lifetime_points": row.lifetime_points,
                "events_attended": row.total_events_joined,
                "badge_name": row.badge_name,
                "badge_color": row.badge_color,
            })

        return entries, total

    async def get_leaderboard_periodic(
        self,
        period: str = "weekly",
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[dict], int]:
        """Get leaderboard for a specific time period (weekly/monthly)."""
        now = datetime.utcnow()
        if period == "weekly":
            start_date = now - timedelta(days=7)
        elif period == "monthly":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)  # default to weekly

        count_stmt = (
            select(func.count(func.distinct(UserRewardLedger.user_id)))
            .select_from(UserRewardLedger)
            .where(
                and_(
                    UserRewardLedger.created_at >= start_date,
                    UserRewardLedger.points_delta > 0,
                )
            )
        )
        total = await self._session.scalar(count_stmt) or 0

        offset = (page - 1) * page_size

        period_points_subq = (
            select(
                UserRewardLedger.user_id,
                func.sum(UserRewardLedger.points_delta).label("period_points"),
            )
            .where(
                and_(
                    UserRewardLedger.created_at >= start_date,
                    UserRewardLedger.points_delta > 0,
                )
            )
            .group_by(UserRewardLedger.user_id)
            .subquery()
        )

        stmt = (
            select(
                period_points_subq.c.user_id,
                period_points_subq.c.period_points,
                User.first_names,
                User.last_name,
                UserRewardProfile.total_events_joined,
                RewardLevel.name.label("badge_name"),
                RewardLevel.badge_color,
            )
            .join(User, period_points_subq.c.user_id == User.id)
            .outerjoin(UserRewardProfile, period_points_subq.c.user_id == UserRewardProfile.user_id)
            .outerjoin(RewardLevel, UserRewardProfile.level_id == RewardLevel.id)
            .order_by(period_points_subq.c.period_points.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        entries = []
        for idx, row in enumerate(rows):
            entries.append({
                "rank": offset + idx + 1,
                "user_id": row.user_id,
                "first_name": row.first_names,
                "last_name": row.last_name,
                "lifetime_points": int(row.period_points or 0),
                "events_attended": row.total_events_joined or 0,
                "badge_name": row.badge_name,
                "badge_color": row.badge_color,
            })

        return entries, total

    async def get_user_rank(self, user_id: str) -> Optional[int]:
        """Get user's rank on the all-time leaderboard."""
        profile = await self.get_user_profile(user_id)
        if not profile or profile.lifetime_points == 0:
            return None

        count_stmt = (
            select(func.count())
            .select_from(UserRewardProfile)
            .where(UserRewardProfile.lifetime_points > profile.lifetime_points)
        )
        users_above = await self._session.scalar(count_stmt) or 0
        return users_above + 1

    async def get_user_interest_names(self, user_id: str) -> List[str]:
        """Return the user's configured interest names."""
        stmt = (
            select(User)
            .options(selectinload(User.interests))
            .where(User.id == user_id)
        )
        user = await self._session.scalar(stmt)
        if not user:
            return []
        return [interest.name for interest in user.interests]

    async def get_user_purchased_event_ids(self, user_id: str) -> List[str]:
        """Return event ids that the user has already purchased tickets for."""
        stmt = (
            select(Ticket.event_id)
            .where(Ticket.owner_id == user_id)
            .distinct()
        )
        result = await self._session.scalars(stmt)
        return [event_id for event_id in result.all() if event_id]

    async def list_upcoming_recommendation_events(
        self,
        *,
        exclude_event_ids: Optional[List[str]] = None,
        pool_size: int = 50,
    ) -> List[Event]:
        """Return upcoming approved events with category and ticket types loaded."""
        conditions = [
            Event.status == "approved",
            or_(
                Event.start_date > func.current_date(),
                and_(
                    Event.start_date == func.current_date(),
                    Event.start_time > func.current_time(),
                ),
            ),
        ]

        if exclude_event_ids:
            conditions.append(Event.id.notin_(exclude_event_ids))

        stmt = (
            select(Event)
            .where(*conditions)
            .options(
                selectinload(Event.category),
                selectinload(Event.ticket_types),
            )
            .order_by(Event.start_date.asc(), Event.start_time.asc(), Event.title.asc())
            .limit(max(1, pool_size))
        )
        result = await self._session.scalars(stmt)
        return list(result.all())
