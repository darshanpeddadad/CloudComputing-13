from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from datetime import datetime

from app.rewards.rules.point_rules import REDEMPTION_CONFIG
from app.rewards.schemas import (
    RedemptionPreviewResponse,
    RedemptionReceiptResponse,
)

if TYPE_CHECKING:
    from app.rewards.repositories import RewardRepository
    from app.rewards.models import UserRewardProfile


class RedemptionService:

    def __init__(self, repository: "RewardRepository"):
        self._repository = repository
        self._config = REDEMPTION_CONFIG

    async def preview_redemption(
        self,
        user_id: str,
        points_to_redeem: int,
        event_id: Optional[str] = None,
        ticket_price: Optional[float] = None,
    ) -> RedemptionPreviewResponse:

        profile = await self._repository.get_user_profile(user_id)
        
        if not profile:
            return RedemptionPreviewResponse(
                points_to_redeem=points_to_redeem,
                points_actually_used=0,
                discount_amount=0.0,
                currency=self._config["currency"],
                current_balance=0,
                balance_after_redemption=0,
                is_valid=False,
                validation_message="User reward profile not found",
            )
        
        is_valid, message = self._validate_redemption(profile, points_to_redeem)
        
        if not is_valid:
            return RedemptionPreviewResponse(
                points_to_redeem=points_to_redeem,
                points_actually_used=0,
                discount_amount=0.0,
                currency=self._config["currency"],
                current_balance=profile.current_points,
                balance_after_redemption=profile.current_points,
                is_valid=False,
                validation_message=message,
            )
        
        # Calculate raw discount
        raw_discount = self._calculate_discount(points_to_redeem)
        
        # Apply max discount cap if ticket price is provided
        max_discount_amount = None
        discount_capped = False
        points_actually_used = points_to_redeem
        final_discount = raw_discount
        
        if ticket_price is not None and ticket_price > 0:
            max_discount_percentage = self._config["max_discount_percentage"]
            max_discount_amount = round(ticket_price * (max_discount_percentage / 100), 2)
            
            if raw_discount > max_discount_amount:
                discount_capped = True
                final_discount = max_discount_amount
                # Calculate actual points that would be used for capped discount
                rate = self._config["points_to_currency_rate"]
                points_actually_used = int(max_discount_amount / rate)
        
        return RedemptionPreviewResponse(
            points_to_redeem=points_to_redeem,
            points_actually_used=points_actually_used,
            discount_amount=final_discount,
            max_discount_amount=max_discount_amount,
            discount_capped=discount_capped,
            currency=self._config["currency"],
            current_balance=profile.current_points,
            balance_after_redemption=profile.current_points - points_actually_used,
            is_valid=True,
            validation_message=f"Discount capped at {self._config['max_discount_percentage']}% of ticket price" if discount_capped else None,
        )

    async def redeem_points(
        self,
        user_id: str,
        points_to_redeem: int,
        redemption_type: str = "discount",
        event_id: Optional[str] = None,
    ) -> RedemptionReceiptResponse:
        
        profile = await self._repository.get_or_create_user_profile(user_id)
        
        is_valid, message = self._validate_redemption(profile, points_to_redeem)
        if not is_valid:
            raise ValueError(message)
        
        discount_amount = self._calculate_discount(points_to_redeem)
   
        await self._repository.update_user_profile(
            profile,
            points_delta=-points_to_redeem,
        )
        
        ledger_entry = await self._repository.create_ledger_entry(
            user_id=user_id,
            points_delta=-points_to_redeem,
            reason="redemption_discount",
            description=f"Redeemed {points_to_redeem} points for {self._config['currency']} {discount_amount:.2f} discount",
            event_id=event_id,
            metadata={
                "redemption_type": redemption_type,
                "discount_amount": discount_amount,
                "currency": self._config["currency"],
                "points_to_currency_rate": self._config["points_to_currency_rate"],
            },
        )
        
        return RedemptionReceiptResponse(
            transaction_id=ledger_entry.id,
            points_redeemed=points_to_redeem,
            discount_amount=discount_amount,
            currency=self._config["currency"],
            new_balance=profile.current_points,
            redemption_type=redemption_type,
            event_id=event_id,
            created_at=ledger_entry.created_at,
        )

    def _validate_redemption(
        self,
        profile: "UserRewardProfile",
        points_to_redeem: int,
    ) -> tuple[bool, Optional[str]]:
        """Validate a redemption request."""
        min_points = self._config["min_redemption_points"]
        if points_to_redeem < min_points:
            return False, f"Minimum redemption is {min_points} points"
        
        if profile.current_points < points_to_redeem:
            return False, f"Insufficient points. Available: {profile.current_points}"
        
        return True, None

    def _calculate_discount(self, points: int) -> float:
        """Calculate discount amount for given points."""
        rate = self._config["points_to_currency_rate"]
        return round(points * rate, 2)

    def get_redemption_rate(self) -> dict:
        """Get current redemption rate configuration."""
        return {
            "points_to_currency_rate": self._config["points_to_currency_rate"],
            "currency": self._config["currency"],
            "min_redemption_points": self._config["min_redemption_points"],
            "max_discount_percentage": self._config["max_discount_percentage"],
        }
