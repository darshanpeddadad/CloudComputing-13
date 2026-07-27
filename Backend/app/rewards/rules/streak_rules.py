from typing import Dict, Any

STREAK_CONFIG: Dict[str, Any] = {
    "period": "weekly",
    "multipliers": {
        0: 1.0,
        2: 1.1,
        3: 1.2,
        4: 1.3,
        6: 1.4,
        8: 1.5,
        10: 1.6,
        12: 1.75,
        16: 1.9,
        20: 2.0,
    },
    "milestones": [3, 5, 8, 12, 20, 52],
    "grace_period_weeks": 0,
}


def get_streak_multiplier(streak_length: int) -> float:
    multipliers = STREAK_CONFIG["multipliers"]
    applicable_multiplier = 1.0
    
    for threshold in sorted(multipliers.keys()):
        if streak_length >= threshold:
            applicable_multiplier = multipliers[threshold]
        else:
            break
    
    return applicable_multiplier


def get_next_streak_milestone(current_streak: int) -> tuple[int, float] | None:
    multipliers = STREAK_CONFIG["multipliers"]
    
    for threshold in sorted(multipliers.keys()):
        if threshold > current_streak:
            return threshold, multipliers[threshold]
    
    return None


def get_streak_bonus_percentage(streak_length: int) -> int:
    multiplier = get_streak_multiplier(streak_length)
    return int((multiplier - 1.0) * 100)


def is_milestone(streak_length: int) -> bool:
    return streak_length in STREAK_CONFIG["milestones"]
