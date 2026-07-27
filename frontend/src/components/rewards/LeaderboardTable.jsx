import React from "react";
import { Trophy, Medal, Crown, Award, AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

/**
 * Get rank icon based on position
 */
const getRankIcon = (rank) => {
  switch (rank) {
    case 1:
      return <Crown className="w-5 h-5 text-yellow-500" />;
    case 2:
      return <Medal className="w-5 h-5 text-gray-400" />;
    case 3:
      return <Medal className="w-5 h-5 text-amber-600" />;
    default:
      return <span className="font-bold text-muted-foreground">#{rank}</span>;
  }
};

/**
 * LeaderboardTable component - Displays ranked users
 */
const LeaderboardTable = ({
  entries,
  currentUserId,
  loading = false,
  error = null,
  onRetry = null,
  emptyMessage = "No entries yet. Be the first!",
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 space-y-4">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
        <div>
          <p className="text-red-600 dark:text-red-400 font-medium mb-2">
            Failed to load leaderboard
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            {error}
          </p>
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          )}
        </div>
      </div>
    );
  }

  if (!entries || entries.length === 0) {
    return (
      <div className="text-center py-12">
        <Trophy className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="w-16 text-center">Rank</TableHead>
            <TableHead>User</TableHead>
            <TableHead className="text-center">Badge</TableHead>
            <TableHead className="text-center">Events</TableHead>
            <TableHead className="text-right">Points</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.map((entry) => {
            const isCurrentUser = entry.user_id === currentUserId;
            return (
              <TableRow
                key={entry.user_id}
                className={cn(
                  "transition-colors",
                  isCurrentUser && "bg-primary/5 border-primary/20",
                  entry.rank <= 3 && "bg-gradient-to-r",
                  entry.rank === 1 &&
                    "from-yellow-50 to-transparent dark:from-yellow-900/10",
                  entry.rank === 2 &&
                    "from-gray-100 to-transparent dark:from-gray-800/30",
                  entry.rank === 3 &&
                    "from-amber-50 to-transparent dark:from-amber-900/10",
                )}
              >
                <TableCell className="text-center">
                  <div className="flex items-center justify-center">
                    {getRankIcon(entry.rank)}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/40 flex items-center justify-center text-sm font-medium">
                      {entry.first_name?.[0]?.toUpperCase()}
                    </div>
                    <div>
                      <span
                        className={cn(
                          "font-medium",
                          isCurrentUser && "text-primary",
                        )}
                      >
                        {entry.first_name} {entry.last_name}
                      </span>
                      {isCurrentUser && (
                        <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                          You
                        </span>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-center">
                  {entry.badge_name ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                      style={{
                        backgroundColor: `${entry.badge_color}20`,
                        color: entry.badge_color,
                      }}
                    >
                      <Award className="w-3 h-3" />
                      {entry.badge_name}
                    </span>
                  ) : (
                    <span className="text-muted-foreground text-xs">—</span>
                  )}
                </TableCell>
                <TableCell className="text-center">
                  <span className="text-muted-foreground">
                    {entry.events_attended}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="font-bold text-lg">
                    {entry.lifetime_points.toLocaleString()}
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

export default LeaderboardTable;
