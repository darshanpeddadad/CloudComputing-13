from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import TYPE_CHECKING
import math

from app.rewards.rules.point_rules import (
    POINT_RULES,
    get_duration_multiplier,
    get_category_multiplier,
    get_capacity_bonus,
)

if TYPE_CHECKING:
    from app.events.models import Event


class PointCalculator:


    def __init__(self):
        self._base_points = POINT_RULES["base_points"]

    def calculate_event_points(self, event: "Event") -> int:

        # Calculate event duration
        duration_hours = self._calculate_duration_hours(event)
        
        # Get multipliers
        duration_mult = get_duration_multiplier(duration_hours)
        
        category_name = event.category.name if event.category else None
        category_mult = get_category_multiplier(category_name)
        
        # Get capacity bonus
        capacity_bonus = get_capacity_bonus(event.max_attendees)
        
        # Calculate final points
        base_calculation = self._base_points * duration_mult * category_mult
        final_points = math.floor(base_calculation) + capacity_bonus
        
        return max(1, final_points)

    def _calculate_duration_hours(self, event: "Event") -> float:
        
        try:
            start_datetime = datetime.combine(event.start_date, event.start_time)
            end_datetime = datetime.combine(event.end_date, event.end_time)
            
            
            if end_datetime < start_datetime:
                end_datetime = end_datetime + timedelta(days=1)
            
            duration = end_datetime - start_datetime
            duration_hours = duration.total_seconds() / 3600
            
            return max(0.5, duration_hours)
        except (TypeError, AttributeError):
            return 1.0

    def get_calculation_breakdown(self, event: "Event") -> dict:

        duration_hours = self._calculate_duration_hours(event)
        duration_mult = get_duration_multiplier(duration_hours)
        category_name = event.category.name if event.category else "Unknown"
        category_mult = get_category_multiplier(category_name)
        capacity_bonus = get_capacity_bonus(event.max_attendees)
        
        base_calculation = self._base_points * duration_mult * category_mult
        final_points = math.floor(base_calculation) + capacity_bonus
        
        return {
            "base_points": self._base_points,
            "duration_hours": round(duration_hours, 2),
            "duration_multiplier": duration_mult,
            "category_name": category_name,
            "category_multiplier": category_mult,
            "capacity": event.max_attendees,
            "capacity_bonus": capacity_bonus,
            "calculated_base": round(base_calculation, 2),
            "final_points": max(1, final_points),
        }
