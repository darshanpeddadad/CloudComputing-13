from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional, List

from app.rewards.models import ParticipationStatus
from app.rewards.schemas import (
    UserRewardProfileResponse,
    RewardLevelResponse,
    PointHistoryResponse,
    PointTransactionResponse,
    PointAwardResult,
    AllBadgesResponse,
    NextEventRecommendationsResponse,
    EventRecommendationItemResponse,
)
from app.rewards.services.point_calculator import PointCalculator
from app.rewards.services.badge_service import BadgeService
from app.rewards.services.streak_service import StreakService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.rewards.repositories import RewardRepository
    from app.events.models import Event
    from app.rewards.models import UserRewardProfile


class RewardService:

    def __init__(
        self,
        repository: "RewardRepository",
        point_calculator: PointCalculator,
        badge_service: BadgeService,
        streak_service: Optional[StreakService] = None,
    ):
        self._repository = repository
        self._point_calculator = point_calculator
        self._badge_service = badge_service
        self._streak_service = streak_service or StreakService(repository)


    async def get_user_profile(
        self,
        user_id: str,
    ) -> Optional[UserRewardProfileResponse]:

        profile = await self._repository.get_user_profile(user_id)
        if not profile:
            return None
        
        return await self._build_profile_response(profile)

    async def get_or_create_user_profile(
        self,
        user_id: str,
    ) -> UserRewardProfileResponse:

        profile = await self._repository.get_or_create_user_profile(user_id)
        return await self._build_profile_response(profile)

    async def _build_profile_response(
        self,
        profile: "UserRewardProfile",
    ) -> UserRewardProfileResponse:
        next_level, points_to_next = await self._badge_service.get_next_badge_info(profile)
        
        current_level_response = None
        if profile.level:
            current_level_response = RewardLevelResponse(
                id=profile.level.id,
                name=profile.level.name,
                description=profile.level.description,
                min_points=profile.level.min_points,
                badge_color=profile.level.badge_color,
                priority=profile.level.priority,
            )
        
        next_level_response = None
        if next_level:
            next_level_response = RewardLevelResponse(
                id=next_level.id,
                name=next_level.name,
                description=next_level.description,
                min_points=next_level.min_points,
                badge_color=next_level.badge_color,
                priority=next_level.priority,
            )
        
        # Calculate streak bonus percentage
        from app.rewards.rules.streak_rules import get_streak_bonus_percentage
        streak_bonus = get_streak_bonus_percentage(profile.current_streak)
        
        return UserRewardProfileResponse(
            user_id=profile.user_id,
            current_points=profile.current_points,
            lifetime_points=profile.lifetime_points,
            total_events_joined=profile.total_events_joined,
            current_level=current_level_response,
            next_level=next_level_response,
            points_to_next_level=points_to_next,
            level_assigned_at=profile.level_assigned_at,
            updated_at=profile.updated_at,
            # Streak fields
            current_streak=profile.current_streak,
            longest_streak=profile.longest_streak,
            streak_multiplier=profile.streak_multiplier,
            streak_bonus_percentage=streak_bonus,
        )

    async def get_point_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> PointHistoryResponse:
      
        page = max(1, page)
        page_size = min(100, max(10, page_size))
        
        transactions, total = await self._repository.get_user_transactions(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        
        transaction_responses = [
            PointTransactionResponse(
                id=t.id,
                user_id=t.user_id,
                event_id=t.event_id,
                points_delta=t.points_delta,
                reason=t.reason,
                description=t.description,
                metadata_json=t.metadata_json,
                created_at=t.created_at,
            )
            for t in transactions
        ]
        
        has_more = (page * page_size) < total
        
        return PointHistoryResponse(
            transactions=transaction_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

  
    async def get_all_badges(self) -> AllBadgesResponse:

        levels = await self._repository.get_all_reward_levels()
        
        badges = [
            RewardLevelResponse(
                id=level.id,
                name=level.name,
                description=level.description,
                min_points=level.min_points,
                badge_color=level.badge_color,
                priority=level.priority,
            )
            for level in levels
        ]
        
        return AllBadgesResponse(
            badges=badges,
            total=len(badges),
        )

    @staticmethod
    def _normalize_tag(value: str) -> str:
        return " ".join(value.lower().strip().split())

    def _is_interest_match(self, normalized_interests: set[str], category_name: str) -> bool:
        if not normalized_interests or not category_name:
            return False

        normalized_category = self._normalize_tag(category_name)
        for interest in normalized_interests:
            if interest == normalized_category:
                return True
            if interest in normalized_category or normalized_category in interest:
                return True
        return False

    @staticmethod
    def _calculate_price_score(price: float, min_price: float, max_price: float) -> float:
        if max_price <= min_price:
            return 1.0
        return max(0.0, min(1.0, 1 - ((price - min_price) / (max_price - min_price))))

    @staticmethod
    def _calculate_time_score(event_date: date) -> float:
        days_until = max((event_date - date.today()).days, 0)
        return max(0.0, 1.0 - (min(days_until, 60) / 60))

    @staticmethod
    def _calculate_discount_score(discount_amount: float, ticket_price: float) -> float:
        if ticket_price <= 0:
            return 1.0
        return max(0.0, min(1.0, discount_amount / ticket_price))

    @staticmethod
    def _calculate_redeemable_discount(current_points: int, ticket_price: float) -> tuple[float, int]:
        from app.rewards.rules.point_rules import REDEMPTION_CONFIG

        min_points = REDEMPTION_CONFIG["min_redemption_points"]
        if current_points < min_points:
            return 0.0, 0

        rate = REDEMPTION_CONFIG["points_to_currency_rate"]
        max_discount_percentage = REDEMPTION_CONFIG["max_discount_percentage"]

        raw_discount = round(current_points * rate, 2)
        capped_discount = round(ticket_price * (max_discount_percentage / 100), 2)
        discount_amount = min(raw_discount, capped_discount)
        points_to_use = int(discount_amount / rate) if rate > 0 else 0
        return round(discount_amount, 2), max(0, points_to_use)

    async def get_next_event_recommendations(
        self,
        user_id: str,
        limit: int = 5,
    ) -> NextEventRecommendationsResponse:
        limit = max(1, min(limit, 20))

        profile = await self._repository.get_or_create_user_profile(user_id)
        current_points = profile.current_points

        user_interests = await self._repository.get_user_interest_names(user_id)
        normalized_interests = {
            self._normalize_tag(interest)
            for interest in user_interests
            if interest and interest.strip()
        }

        purchased_event_ids = await self._repository.get_user_purchased_event_ids(user_id)
        candidate_events = await self._repository.list_upcoming_recommendation_events(
            exclude_event_ids=purchased_event_ids,
            pool_size=max(limit * 8, 30),
        )

        scored_candidates: list[dict] = []
        for event in candidate_events:
            valid_ticket_types = [tt for tt in event.ticket_types if tt.price is not None]
            if not valid_ticket_types:
                continue

            cheapest_ticket = min(valid_ticket_types, key=lambda tt: float(tt.price))
            min_price = round(float(cheapest_ticket.price), 2)
            currency = cheapest_ticket.currency or "USD"
            discount_amount, points_to_use = self._calculate_redeemable_discount(current_points, min_price)

            category_name = event.category.name if event.category else "General"
            interest_match = self._is_interest_match(normalized_interests, category_name)

            scored_candidates.append(
                {
                    "event": event,
                    "category": category_name,
                    "min_ticket_price": min_price,
                    "currency": currency,
                    "discount_amount": discount_amount,
                    "points_to_use": points_to_use,
                    "estimated_final_price": round(max(min_price - discount_amount, 0.0), 2),
                    "interest_match": interest_match,
                    "time_score": self._calculate_time_score(event.start_date),
                }
            )

        if not scored_candidates:
            return NextEventRecommendationsResponse(
                current_points=current_points,
                used_interest_factor=False,
                fallback_applied=False,
                total_candidates=0,
                recommendations=[],
            )

        has_interest_match = any(item["interest_match"] for item in scored_candidates)
        fallback_applied = bool(normalized_interests) and not has_interest_match

        min_candidate_price = min(item["min_ticket_price"] for item in scored_candidates)
        max_candidate_price = max(item["min_ticket_price"] for item in scored_candidates)

        for candidate in scored_candidates:
            discount_score = self._calculate_discount_score(
                candidate["discount_amount"],
                candidate["min_ticket_price"],
            )
            price_score = self._calculate_price_score(
                candidate["min_ticket_price"],
                min_candidate_price,
                max_candidate_price,
            )
            interest_score = 1.0 if candidate["interest_match"] else 0.0

            if has_interest_match:
                recommendation_score = (
                    (0.45 * interest_score)
                    + (0.35 * discount_score)
                    + (0.20 * candidate["time_score"])
                )
            else:
                recommendation_score = (
                    (0.45 * discount_score)
                    + (0.30 * candidate["time_score"])
                    + (0.25 * price_score)
                )

            reasons: list[str] = []
            if has_interest_match and candidate["interest_match"]:
                reasons.append("matches_interest")
            if candidate["discount_amount"] > 0:
                reasons.append("points_discount_available")
            else:
                reasons.append("budget_friendly")
            if candidate["time_score"] >= 0.7:
                reasons.append("happening_soon")

            candidate["recommendation_score"] = round(recommendation_score, 4)
            candidate["reasons"] = reasons

        scored_candidates.sort(
            key=lambda item: (
                -item["recommendation_score"],
                item["event"].start_date,
                item["event"].start_time,
            )
        )

        top_candidates = scored_candidates[:limit]
        recommendations = [
            EventRecommendationItemResponse(
                event_id=item["event"].id,
                title=item["event"].title,
                category=item["category"],
                location=item["event"].location,
                start_date=item["event"].start_date,
                start_time=item["event"].start_time,
                min_ticket_price=item["min_ticket_price"],
                currency=item["currency"],
                potential_discount=item["discount_amount"],
                points_to_use=item["points_to_use"],
                estimated_final_price=item["estimated_final_price"],
                recommendation_score=item["recommendation_score"],
                interest_match=item["interest_match"],
                reasons=item["reasons"],
            )
            for item in top_candidates
        ]

        return NextEventRecommendationsResponse(
            current_points=current_points,
            used_interest_factor=has_interest_match,
            fallback_applied=fallback_applied,
            total_candidates=len(scored_candidates),
            recommendations=recommendations,
        )

    async def _apply_streak_bonus(
        self,
        user_id: str,
        base_points: int,
    ) -> tuple[int, dict]:
        streak_result = await self._streak_service.update_streak_on_activity(user_id)
        streak_multiplier = streak_result.get("multiplier", 1.0)
        final_points = int(base_points * streak_multiplier)
        
        return final_points, streak_result

    async def award_points_for_purchase(
        self,
        user_id: str,
        event_id: str,
        ticket_id: str,
    ) -> PointAwardResult:

        from app.events.models import Event
        
        already_awarded = await self._repository.check_points_already_awarded(
            user_id=user_id,
            event_id=event_id,
            reason="ticket_purchase",
        )
        
        if already_awarded:
            profile = await self._repository.get_or_create_user_profile(user_id)
            return PointAwardResult(
                success=False,
                points_awarded=0,
                new_balance=profile.current_points,
                new_lifetime_total=profile.lifetime_points,
                badge_upgraded=False,
                new_badge=None,
                message="Points already awarded for this purchase",
            )
        
        event = await self._repository._session.get(Event, event_id)
        if not event:
            profile = await self._repository.get_or_create_user_profile(user_id)
            return PointAwardResult(
                success=False,
                points_awarded=0,
                new_balance=profile.current_points,
                new_lifetime_total=profile.lifetime_points,
                badge_upgraded=False,
                new_badge=None,
                message="Event not found",
            )
        
        # Calculate base points from event
        base_points = self._point_calculator.calculate_event_points(event)
        
        # Apply streak bonus
        final_points, streak_result = await self._apply_streak_bonus(user_id, base_points)
        streak_multiplier = streak_result.get("multiplier", 1.0)
        
        profile = await self._repository.get_or_create_user_profile(user_id)
        
        await self._repository.update_user_profile(
            profile,
            points_delta=final_points,
            increment_events=True,
        )
        
        calculation_breakdown = self._point_calculator.get_calculation_breakdown(event)
        # Add streak info to breakdown
        calculation_breakdown["streak_multiplier"] = streak_multiplier
        calculation_breakdown["base_points_before_streak"] = base_points
        calculation_breakdown["final_points"] = final_points
        calculation_breakdown["current_streak"] = streak_result.get("current_streak", 0)
        
        await self._repository.create_ledger_entry(
            user_id=user_id,
            points_delta=final_points,
            reason="ticket_purchase",
            description=f"Purchased ticket for event: {event.title}",
            event_id=event_id,
            ticket_id=ticket_id,
            metadata={
                "event_title": event.title,
                "calculation": calculation_breakdown,
            },
        )
        
        badge_upgraded, new_badge = await self._badge_service.check_and_upgrade_badge(
            profile
        )
        
        new_badge_response = None
        if new_badge:
            new_badge_response = RewardLevelResponse(
                id=new_badge.id,
                name=new_badge.name,
                description=new_badge.description,
                min_points=new_badge.min_points,
                badge_color=new_badge.badge_color,
                priority=new_badge.priority,
            )
        
        participation = await self._repository.get_participation(user_id, event_id)
        if not participation:
            await self._repository.create_participation(
                user_id=user_id,
                event_id=event_id,
                ticket_id=ticket_id,
                status=ParticipationStatus.REGISTERED.value,
            )
        
        # Build message with streak info
        message = f"Earned {final_points} points for purchasing ticket"
        if streak_multiplier > 1.0:
            bonus_pct = int((streak_multiplier - 1.0) * 100)
            message += f" (includes {bonus_pct}% streak bonus!)"
        if badge_upgraded:
            message += f" Congratulations! You've earned the {new_badge.name} badge!"
        
        return PointAwardResult(
            success=True,
            points_awarded=final_points,
            new_balance=profile.current_points,
            new_lifetime_total=profile.lifetime_points,
            badge_upgraded=badge_upgraded,
            new_badge=new_badge_response,
            message=message,
            streak_info={
                "current_streak": streak_result.get("current_streak", 0),
                "streak_multiplier": streak_multiplier,
                "bonus_percentage": streak_result.get("bonus_percentage", 0),
                "streak_increased": streak_result.get("streak_status") == "increased",
                "hit_milestone": streak_result.get("hit_milestone", False),
            },
        )

    async def redeem_points_for_purchase(
        self,
        user_id: str,
        points_to_redeem: int,
        event_id: str,
        ticket_price: float,
    ) -> dict:
        
        from app.rewards.rules.point_rules import REDEMPTION_CONFIG
        
        profile = await self._repository.get_or_create_user_profile(user_id)
        
        min_points = REDEMPTION_CONFIG["min_redemption_points"]
        if points_to_redeem < min_points:
            raise ValueError(f"Minimum redemption is {min_points} points")
        
        if profile.current_points < points_to_redeem:
            raise ValueError(f"Insufficient points. Available: {profile.current_points}")
        
        rate = REDEMPTION_CONFIG["points_to_currency_rate"]
        raw_discount = round(points_to_redeem * rate, 2)
        
        # Apply max discount percentage cap
        max_discount_percentage = REDEMPTION_CONFIG["max_discount_percentage"]
        max_discount_amount = round(ticket_price * (max_discount_percentage / 100), 2)
        
        discount_capped = False
        points_actually_used = points_to_redeem
        discount_amount = raw_discount
        
        if raw_discount > max_discount_amount:
            discount_capped = True
            discount_amount = max_discount_amount
            # Calculate actual points to deduct for capped discount
            points_actually_used = int(max_discount_amount / rate)
        
        await self._repository.update_user_profile(
            profile,
            points_delta=-points_actually_used,
        )
        
        description = f"Redeemed {points_actually_used} points for €{discount_amount:.2f} discount"
        if discount_capped:
            description += f" (capped at {max_discount_percentage}% of ticket price)"
        
        await self._repository.create_ledger_entry(
            user_id=user_id,
            points_delta=-points_actually_used,
            reason="redemption_purchase",
            description=description,
            event_id=event_id,
            ticket_id=None,
            metadata={
                "redemption_type": "ticket_purchase_discount",
                "discount_amount": discount_amount,
                "currency": REDEMPTION_CONFIG["currency"],
                "discount_capped": discount_capped,
                "max_discount_percentage": max_discount_percentage,
                "ticket_price": ticket_price,
                "points_requested": points_to_redeem,
                "points_actually_used": points_actually_used,
            },
        )
        
        return {
            "points_redeemed": points_actually_used,
            "discount_amount": discount_amount,
            "new_balance": profile.current_points,
            "discount_capped": discount_capped,
        }
