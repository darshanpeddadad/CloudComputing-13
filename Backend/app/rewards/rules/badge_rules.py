from typing import Dict, List, Optional, Any

BADGE_THRESHOLDS: List[Dict[str, Any]] = [
    {
        "id": "bronze",
        "name": "Bronze",
        "description": "Welcome to the community! Keep attending events to level up.",
        "min_points": 500,
        "badge_color": "#CD7F32",
        "priority": 1,
    },
    {
        "id": "silver",
        "name": "Silver",
        "description": "You're becoming a regular! Your dedication is showing.",
        "min_points": 1500,
        "badge_color": "#C0C0C0",
        "priority": 2,
    },
    {
        "id": "gold",
        "name": "Gold",
        "description": "A true event enthusiast! You're among our top members.",
        "min_points": 3000,
        "badge_color": "#FFD700",
        "priority": 3,
    },
    {
        "id": "platinum",
        "name": "Platinum",
        "description": "Elite status achieved! You're a cornerstone of our community.",
        "min_points": 6000,
        "badge_color": "#E5E4E2",
        "priority": 4,
    },
]


def get_badge_for_points(total_points: int) -> Optional[Dict[str, Any]]:

    qualifying_badges = [
        badge for badge in BADGE_THRESHOLDS 
        if total_points >= badge["min_points"]
    ]
    
    if not qualifying_badges:
        return None
    
    return max(qualifying_badges, key=lambda b: b["min_points"])


def get_next_badge(total_points: int) -> Optional[Dict[str, Any]]:

    next_badges = [
        badge for badge in BADGE_THRESHOLDS 
        if total_points < badge["min_points"]
    ]
    
    if not next_badges:
        return None
    
    return min(next_badges, key=lambda b: b["min_points"])


def get_points_to_next_badge(total_points: int) -> Optional[int]:

    next_badge = get_next_badge(total_points)
    if not next_badge:
        return None
    return next_badge["min_points"] - total_points
