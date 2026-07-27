from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RewardLevelResponse(BaseModel):
    """Response schema for a reward level/badge."""
    id: str
    name: str
    description: Optional[str] = None
    min_points: int
    badge_color: Optional[str] = None
    priority: int

    class Config:
        from_attributes = True


class AllBadgesResponse(BaseModel):
    """Response schema for listing all available badges."""
    badges: List[RewardLevelResponse]
    total: int


class UserRewardProfileResponse(BaseModel):
    """Response schema for user's reward profile."""
    user_id: str
    current_points: int = Field(description="Points available for redemption")
    lifetime_points: int = Field(description="Total points ever earned")
    total_events_joined: int
    current_level: Optional[RewardLevelResponse] = None
    next_level: Optional[RewardLevelResponse] = None
    points_to_next_level: Optional[int] = None
    level_assigned_at: Optional[datetime] = None
    updated_at: datetime
    
    # Streak info
    current_streak: int = Field(default=0, description="Current consecutive weeks of activity")
    longest_streak: int = Field(default=0, description="Longest streak ever achieved")
    streak_multiplier: float = Field(default=1.0, description="Current point multiplier from streak")
    streak_bonus_percentage: int = Field(default=0, description="Bonus percentage from streak")

    class Config:
        from_attributes = True


class UserPublicRewardStats(BaseModel):
    """Public-facing reward stats for leaderboard."""
    user_id: str
    first_name: str
    last_name: str
    lifetime_points: int
    events_attended: int
    badge_name: Optional[str] = None
    badge_color: Optional[str] = None
    rank: int


class PointTransactionResponse(BaseModel):
    """Response schema for a point transaction."""
    id: str
    user_id: str
    event_id: Optional[str] = None
    points_delta: int = Field(description="Positive for earned, negative for redeemed")
    reason: str
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PointHistoryResponse(BaseModel):
    """Paginated point transaction history."""
    transactions: List[PointTransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class LeaderboardEntry(BaseModel):
    """Single entry in the leaderboard."""
    rank: int
    user_id: str
    first_name: str
    last_name: str
    lifetime_points: int
    events_attended: int
    badge_name: Optional[str] = None
    badge_color: Optional[str] = None


class LeaderboardResponse(BaseModel):
    """Paginated leaderboard response."""
    entries: List[LeaderboardEntry]
    total_users: int
    page: int
    page_size: int
    period: str = Field(description="all_time, weekly, or monthly")



class RedemptionPreviewRequest(BaseModel):
    """Request schema for previewing a redemption."""
    points_to_redeem: int = Field(gt=0, description="Number of points to redeem")
    event_id: Optional[str] = Field(None, description="Optional event for context-specific redemption")
    ticket_price: Optional[float] = Field(None, gt=0, description="Ticket price to calculate max discount cap")


class RedemptionPreviewResponse(BaseModel):
    """Response schema for redemption preview."""
    points_to_redeem: int
    points_actually_used: int  # May be less if capped by max_discount_percentage
    discount_amount: float
    max_discount_amount: Optional[float] = None  # Max allowed based on ticket price
    discount_capped: bool = False  # Whether discount was capped
    currency: str
    current_balance: int
    balance_after_redemption: int
    is_valid: bool
    validation_message: Optional[str] = None


class RedeemPointsRequest(BaseModel):
    """Request schema for redeeming points."""
    points_to_redeem: int = Field(gt=0, description="Number of points to redeem")
    event_id: Optional[str] = Field(None, description="Event to apply discount to")
    redemption_type: str = Field(default="discount", description="Type of redemption")


class RedemptionReceiptResponse(BaseModel):
    """Response schema after successful redemption."""
    transaction_id: str
    points_redeemed: int
    discount_amount: float
    currency: str
    new_balance: int
    redemption_type: str
    event_id: Optional[str] = None
    created_at: datetime


class EventParticipationResponse(BaseModel):
    """Response schema for event participation record."""
    id: str
    event_id: str
    user_id: str
    ticket_id: Optional[str] = None
    status: str
    registered_at: datetime
    checked_in_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PointAwardResult(BaseModel):
    """Result of awarding points to a user."""
    success: bool
    points_awarded: int
    new_balance: int
    new_lifetime_total: int
    badge_upgraded: bool
    new_badge: Optional[RewardLevelResponse] = None
    message: str
    streak_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Streak information including current_streak, multiplier, bonus_percentage"
    )


class StreakInfoResponse(BaseModel):
    """Response schema for user's streak information."""
    current_streak: int = Field(description="Current consecutive weeks of activity")
    longest_streak: int = Field(description="Best streak ever achieved")
    streak_multiplier: float = Field(description="Current point multiplier (1.0 to 2.0)")
    bonus_percentage: int = Field(description="Bonus percentage (0 to 100)")
    last_activity_week: Optional[str] = Field(description="Last activity week in ISO format (e.g., 2026-W04)")
    streak_is_active: bool = Field(description="Whether streak is currently active")
    streak_at_risk: bool = Field(description="Whether streak will be lost if no activity this week")
    next_milestone: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Next streak milestone info (weeks, multiplier, bonus_percentage)"
    )
    weeks_to_next_milestone: Optional[int] = Field(
        default=None,
        description="Weeks remaining to reach next milestone"
    )


class EventRecommendationItemResponse(BaseModel):
    """Single personalized event recommendation."""
    event_id: str
    title: str
    category: str
    location: str
    start_date: date
    start_time: time
    min_ticket_price: float
    currency: str
    potential_discount: float
    points_to_use: int
    estimated_final_price: float
    recommendation_score: float
    interest_match: bool
    reasons: List[str]


class NextEventRecommendationsResponse(BaseModel):
    """Recommendation list computed for a user."""
    current_points: int
    used_interest_factor: bool
    fallback_applied: bool
    total_candidates: int
    recommendations: List[EventRecommendationItemResponse]
