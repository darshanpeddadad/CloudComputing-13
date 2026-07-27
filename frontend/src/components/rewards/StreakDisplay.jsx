import React, { useMemo } from "react";
import {
  Flame,
  Target,
  TrendingUp,
  AlertTriangle,
  Zap,
  Calendar,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * StreakDisplay - Shows user's current streak information
 */
const StreakDisplay = ({ streak, loading = false }) => {
  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!streak) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            <Flame className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Start attending events to build your streak!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    current_streak = 0,
    longest_streak = 0,
    streak_multiplier = 1.0,
    bonus_percentage = 0,
    streak_is_active = false,
    streak_at_risk = false,
    next_milestone = null,
    weeks_to_next_milestone = null,
  } = streak;

  // Calculate progress to next milestone (memoized to avoid recalculation on every render)
  const progressToMilestone = useMemo(() => {
    return next_milestone
      ? (current_streak / next_milestone.weeks) * 100
      : 100;
  }, [current_streak, next_milestone]);

  return (
    <div className="space-y-4">
      {/* Main Streak Card */}
      <Card
        className={cn(
          "overflow-hidden transition-all",
          streak_at_risk && "border-amber-500/50",
          current_streak >= 4 && "border-orange-500/30",
        )}
      >
        {/* Gradient Header based on streak level */}
        <div
          className={cn(
            "h-2",
            current_streak === 0 && "bg-gray-300 dark:bg-gray-700",
            current_streak >= 1 &&
              current_streak < 4 &&
              "bg-gradient-to-r from-yellow-400 to-orange-400",
            current_streak >= 4 &&
              current_streak < 8 &&
              "bg-gradient-to-r from-orange-400 to-red-500",
            current_streak >= 8 &&
              current_streak < 12 &&
              "bg-gradient-to-r from-red-500 to-pink-500",
            current_streak >= 12 &&
              "bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500",
          )}
        />

        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Flame
                className={cn(
                  "w-6 h-6",
                  current_streak === 0 && "text-gray-400",
                  current_streak >= 1 &&
                    current_streak < 4 &&
                    "text-orange-500",
                  current_streak >= 4 && current_streak < 8 && "text-red-500",
                  current_streak >= 8 && "text-pink-500 animate-pulse",
                )}
              />
              Activity Streak
            </CardTitle>
            {streak_at_risk && (
              <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400 text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>At risk!</span>
              </div>
            )}
          </div>
          <CardDescription>
            Attend events weekly to maintain your streak and earn bonus points
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Current Streak Display */}
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div
                className={cn(
                  "text-6xl font-bold",
                  current_streak === 0 && "text-gray-400",
                  current_streak >= 1 &&
                    current_streak < 4 &&
                    "text-orange-500",
                  current_streak >= 4 && current_streak < 8 && "text-red-500",
                  current_streak >= 8 &&
                    "bg-gradient-to-r from-red-500 via-pink-500 to-purple-500 bg-clip-text text-transparent",
                )}
              >
                {current_streak}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {current_streak === 1 ? "week" : "weeks"} in a row
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            {/* Multiplier */}
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <Zap className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <div className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                {streak_multiplier.toFixed(1)}x
              </div>
              <div className="text-xs text-muted-foreground">Multiplier</div>
            </div>

            {/* Bonus Percentage */}
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <TrendingUp className="w-5 h-5 mx-auto mb-1 text-green-500" />
              <div className="text-xl font-bold text-green-600 dark:text-green-400">
                +{bonus_percentage}%
              </div>
              <div className="text-xs text-muted-foreground">Bonus</div>
            </div>

            {/* Best Streak */}
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <Target className="w-5 h-5 mx-auto mb-1 text-purple-500" />
              <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
                {longest_streak}
              </div>
              <div className="text-xs text-muted-foreground">Best</div>
            </div>
          </div>

          {/* Progress to Next Milestone */}
          {next_milestone && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Next: {next_milestone.multiplier}x ({next_milestone.weeks}{" "}
                  weeks)
                </span>
                <span className="font-medium">
                  {weeks_to_next_milestone} week
                  {weeks_to_next_milestone !== 1 ? "s" : ""} to go
                </span>
              </div>
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-orange-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(progressToMilestone, 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* At Risk Warning */}
          {streak_at_risk && current_streak > 0 && (
            <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-amber-800 dark:text-amber-200">
                  Your streak is at risk!
                </p>
                <p className="text-amber-700 dark:text-amber-300 mt-1">
                  Attend an event this week to keep your {current_streak}-week
                  streak alive.
                </p>
              </div>
            </div>
          )}

          {/* Max Streak Achieved */}
          {streak_multiplier >= 2.0 && (
            <div className="flex items-center justify-center gap-2 p-3 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg">
              <span className="text-2xl">🔥</span>
              <span className="font-medium text-purple-700 dark:text-purple-300">
                Maximum multiplier achieved!
              </span>
              <span className="text-2xl">🔥</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * StreakMultiplierTiers - Shows all available multiplier tiers
 */
export const StreakMultiplierTiers = ({
  multipliers = [],
  currentStreak = 0,
}) => {
  if (!multipliers.length) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-500" />
          Streak Multiplier Tiers
        </CardTitle>
        <CardDescription>
          Keep your streak going to unlock higher point multipliers
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {multipliers.map((tier, index) => {
            const isUnlocked = currentStreak >= tier.weeks;
            const isCurrent =
              currentStreak >= tier.weeks &&
              (index === multipliers.length - 1 ||
                currentStreak < multipliers[index + 1]?.weeks);

            return (
              <div
                key={tier.weeks}
                className={cn(
                  "p-3 rounded-lg border text-center transition-all",
                  isUnlocked
                    ? "bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 border-orange-200 dark:border-orange-800"
                    : "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 opacity-60",
                  isCurrent &&
                    "ring-2 ring-orange-500 ring-offset-2 dark:ring-offset-gray-950",
                )}
              >
                <div
                  className={cn(
                    "text-lg font-bold",
                    isUnlocked
                      ? "text-orange-600 dark:text-orange-400"
                      : "text-gray-400",
                  )}
                >
                  {tier.multiplier}x
                </div>
                <div className="text-xs text-muted-foreground">
                  {tier.weeks} week{tier.weeks !== 1 ? "s" : ""}
                </div>
                <div
                  className={cn(
                    "text-xs mt-1",
                    isUnlocked
                      ? "text-green-600 dark:text-green-400"
                      : "text-muted-foreground",
                  )}
                >
                  +{tier.bonus_percentage}%
                </div>
                {isCurrent && (
                  <div className="text-xs text-orange-600 dark:text-orange-400 mt-1 font-medium">
                    Current
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * StreakBadge - Compact streak badge for display in other components
 */
export const StreakBadge = ({ streak, size = "sm" }) => {
  if (!streak || streak.current_streak === 0) {
    return null;
  }

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        "bg-gradient-to-r from-orange-100 to-red-100 dark:from-orange-900/30 dark:to-red-900/30",
        "text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800",
        sizeClasses[size],
      )}
    >
      <Flame
        className={cn(
          size === "sm" && "w-3 h-3",
          size === "md" && "w-4 h-4",
          size === "lg" && "w-5 h-5",
        )}
      />
      <span>{streak.current_streak}</span>
      {streak.streak_multiplier > 1 && (
        <span className="text-yellow-600 dark:text-yellow-400">
          ({streak.streak_multiplier}x)
        </span>
      )}
    </div>
  );
};

export default StreakDisplay;
