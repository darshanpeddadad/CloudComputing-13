import React from "react";
import { Award, Star } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * BadgeDisplay component - Shows a user's current badge with styling
 */
const BadgeDisplay = ({ badge, size = "medium", showDescription = true }) => {
  if (!badge) {
    return (
      <div className="flex flex-col items-center p-4 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-2">
          <Award className="w-8 h-8 text-gray-400" />
        </div>
        <span className="text-sm text-muted-foreground">No badge yet</span>
        <span className="text-xs text-muted-foreground mt-1">
          Earn 500 points to get your first badge!
        </span>
      </div>
    );
  }

  const sizeClasses = {
    small: "w-12 h-12",
    medium: "w-20 h-20",
    large: "w-28 h-28",
  };

  const iconSizes = {
    small: "w-6 h-6",
    medium: "w-10 h-10",
    large: "w-14 h-14",
  };

  return (
    <div className="flex flex-col items-center text-center">
      <div
        className={cn(
          "rounded-full flex items-center justify-center mb-3 shadow-lg transition-transform hover:scale-105",
          sizeClasses[size],
        )}
        style={{
          background: `linear-gradient(135deg, ${badge.badge_color}40, ${badge.badge_color})`,
          border: `3px solid ${badge.badge_color}`,
        }}
      >
        <Star
          className={cn(iconSizes[size], "text-white drop-shadow-md")}
          fill="currentColor"
        />
      </div>
      <h3 className="font-bold text-lg" style={{ color: badge.badge_color }}>
        {badge.name}
      </h3>
      {showDescription && badge.description && (
        <p className="text-sm text-muted-foreground mt-1 max-w-xs">
          {badge.description}
        </p>
      )}
    </div>
  );
};

/**
 * BadgeProgress component - Shows progress to next badge
 */
export const BadgeProgress = ({ currentPoints, nextBadge, pointsToNext }) => {
  if (!nextBadge) {
    return (
      <div className="text-center p-4 bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 rounded-lg">
        <span className="text-amber-600 dark:text-amber-400 font-medium">
          🎉 Maximum level achieved!
        </span>
      </div>
    );
  }

  const progress =
    nextBadge.min_points > 0
      ? ((currentPoints / nextBadge.min_points) * 100).toFixed(1)
      : 0;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">
          Progress to {nextBadge.name}
        </span>
        <span className="font-medium">
          {currentPoints} / {nextBadge.min_points}
        </span>
      </div>
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.min(progress, 100)}%`,
            backgroundColor: nextBadge.badge_color,
          }}
        />
      </div>
      <p className="text-xs text-muted-foreground text-center">
        {pointsToNext} points to go!
      </p>
    </div>
  );
};

/**
 * AllBadges component - Shows all available badges with unlock status
 */
export const AllBadges = ({ badges, currentPoints }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {badges.map((badge) => {
        const isUnlocked = currentPoints >= badge.min_points;
        return (
          <div
            key={badge.id}
            className={cn(
              "p-4 rounded-xl border text-center transition-all",
              isUnlocked
                ? "bg-white dark:bg-gray-800 shadow-md"
                : "bg-gray-50 dark:bg-gray-900 opacity-60",
            )}
          >
            <div
              className={cn(
                "w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2",
                isUnlocked ? "" : "grayscale",
              )}
              style={{
                background: isUnlocked
                  ? `linear-gradient(135deg, ${badge.badge_color}40, ${badge.badge_color})`
                  : "gray",
              }}
            >
              <Star
                className="w-6 h-6 text-white"
                fill={isUnlocked ? "currentColor" : "none"}
              />
            </div>
            <h4 className="font-medium text-sm">{badge.name}</h4>
            <p className="text-xs text-muted-foreground">
              {badge.min_points} points
            </p>
            {isUnlocked && (
              <span className="text-xs text-green-600 dark:text-green-400">
                ✓ Unlocked
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default BadgeDisplay;
