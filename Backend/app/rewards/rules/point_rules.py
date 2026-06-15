from typing import Dict, Any

BASE_POINTS = 10

DURATION_MULTIPLIERS: Dict[str, Dict[str, Any]] = {
    "short": {"max_hours": 1, "multiplier": 1.0},       # Up to 1 hour
    "medium": {"max_hours": 3, "multiplier": 1.5},      # 1-3 hours
    "long": {"max_hours": 6, "multiplier": 2.0},        # 3-6 hours
    "extended": {"max_hours": float("inf"), "multiplier": 2.5},  # 6+ hours
}


CATEGORY_MULTIPLIERS: Dict[str, float] = {
    "workshop": 2.0,
    "conference": 1.8,
    "seminar": 1.7,
    "networking": 1.5,
    "meetup": 1.3,
    "social": 1.2,
    "entertainment": 1.1,
    "default": 1.0,
}

# Capacity bonus
CAPACITY_BONUSES: Dict[str, Dict[str, Any]] = {
    "exclusive": {"max_capacity": 20, "bonus": 5},
    "intimate": {"max_capacity": 50, "bonus": 3},
    "standard": {"max_capacity": float("inf"), "bonus": 0},
}

# Point redemption configuration
REDEMPTION_CONFIG = {
    "points_to_currency_rate": 0.01,  # 1 point = 0.01 EUR
    "min_redemption_points": 100,      # Minimum points required to redeem
    "max_discount_percentage": 50,     # Maximum discount as percentage of event price
    "currency": "EUR",
}


POINT_RULES = {
    "base_points": BASE_POINTS,
    "duration_multipliers": DURATION_MULTIPLIERS,
    "category_multipliers": CATEGORY_MULTIPLIERS,
    "capacity_bonuses": CAPACITY_BONUSES,
    "redemption": REDEMPTION_CONFIG,
}


def get_duration_multiplier(duration_hours: float) -> float:
    """Get the multiplier based on event duration in hours."""
    for tier in ["short", "medium", "long", "extended"]:
        tier_config = DURATION_MULTIPLIERS[tier]
        if duration_hours <= tier_config["max_hours"]:
            return tier_config["multiplier"]
    return DURATION_MULTIPLIERS["extended"]["multiplier"]


def get_category_multiplier(category_name: str) -> float:
    """Get the multiplier based on event category name."""
    if not category_name:
        return CATEGORY_MULTIPLIERS["default"]
    
    category_lower = category_name.lower()
    for key, multiplier in CATEGORY_MULTIPLIERS.items():
        if key in category_lower or category_lower in key:
            return multiplier
    return CATEGORY_MULTIPLIERS["default"]


def get_capacity_bonus(max_attendees: int) -> int:
    """Get bonus points based on event capacity (smaller = more exclusive)."""
    for tier in ["exclusive", "intimate", "standard"]:
        tier_config = CAPACITY_BONUSES[tier]
        if max_attendees <= tier_config["max_capacity"]:
            return tier_config["bonus"]
    return CAPACITY_BONUSES["standard"]["bonus"]
