import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Trophy, ArrowLeft, RefreshCw } from "lucide-react";
import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import LeaderboardTable from "@/components/rewards/LeaderboardTable";
import {
  fetchLeaderboard,
  setLeaderboardPeriod,
} from "@/store/slices/rewardSlice";
import { toast } from "sonner";

const Leaderboard = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const {
    leaderboard,
    leaderboardLoading,
    leaderboardError,
    leaderboardPeriod,
    leaderboardTotal,
  } = useSelector((state) => state.rewards);

  useEffect(() => {
    dispatch(fetchLeaderboard({ period: leaderboardPeriod, pageSize: 100 }));
  }, [dispatch, leaderboardPeriod]);

  // Show error toast when leaderboard fetch fails
  useEffect(() => {
    if (leaderboardError) {
      toast.error("Failed to load leaderboard", {
        description: leaderboardError,
        action: {
          label: "Retry",
          onClick: () => handleRetry(),
        },
      });
    }
  }, [leaderboardError]);

  const handlePeriodChange = (period) => {
    dispatch(setLeaderboardPeriod(period));
    dispatch(fetchLeaderboard({ period, pageSize: 100 }));
  };

  const handleRetry = () => {
    dispatch(fetchLeaderboard({ period: leaderboardPeriod, pageSize: 100 }));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Background Gradients */}
      <div className="fixed inset-0 bg-linear-to-br from-yellow-50 via-white to-amber-50 dark:from-yellow-950/30 dark:via-background dark:to-amber-950/30 -z-10" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(234,179,8,0.15),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(245,158,11,0.12),transparent_50%)] -z-10" />

      <main className="container mx-auto px-4 py-8 md:py-12 relative">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Back Button */}
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>

          {/* Header */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-yellow-400 to-amber-500 shadow-lg">
              <Trophy className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-linear-to-r from-yellow-600 via-amber-500 to-orange-500 bg-clip-text text-transparent">
              Leaderboard
            </h1>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Top event attendees in our community. Earn points by attending
              events and climb the ranks!
            </p>
          </div>

          {/* Period Selector */}
          <div className="flex flex-col sm:flex-row justify-center items-center gap-4">
            <div className="flex gap-2">
              {[
                { value: "all_time", label: "All Time" },
                { value: "monthly", label: "This Month" },
                { value: "weekly", label: "This Week" },
              ].map((period) => (
                <Button
                  key={period.value}
                  variant={
                    leaderboardPeriod === period.value ? "default" : "outline"
                  }
                  size="lg"
                  onClick={() => handlePeriodChange(period.value)}
                  className="min-w-[120px]"
                  disabled={leaderboardLoading}
                >
                  {period.label}
                </Button>
              ))}
            </div>
            
            {/* Retry Button */}
            <Button
              variant="outline"
              size="lg"
              onClick={handleRetry}
              disabled={leaderboardLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${leaderboardLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>

          {/* Stats */}
          <div className="flex justify-center gap-8 text-center">
            <div>
              <p className="text-3xl font-bold text-primary">
                {leaderboardTotal}
              </p>
              <p className="text-sm text-muted-foreground">
                Total Participants
              </p>
            </div>
          </div>

          {/* Leaderboard Card */}
          <Card className="bg-white/80 dark:bg-card/80 backdrop-blur-sm shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-500" />
                {leaderboardPeriod === "all_time"
                  ? "All-Time Rankings"
                  : leaderboardPeriod === "monthly"
                  ? "This Month's Rankings"
                  : "This Week's Rankings"}
              </CardTitle>
              <CardDescription>
                Rankings based on points earned
                {leaderboardPeriod !== "all_time" &&
                  ` during this ${leaderboardPeriod.replace("ly", "")}`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LeaderboardTable
                entries={leaderboard}
                currentUserId={user?.id}
                loading={leaderboardLoading}
                error={leaderboardError}
                onRetry={handleRetry}
                emptyMessage="No rankings yet for this period. Be the first to earn points!"
              />
            </CardContent>
          </Card>

          {/* Info Section */}
          <Card className="bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 border-yellow-200 dark:border-yellow-800">
            <CardContent className="pt-6">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <span className="text-2xl">🏆</span>
                How to Climb the Leaderboard
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="p-3 bg-white/50 dark:bg-black/20 rounded-lg">
                  <h4 className="font-medium mb-1">Attend Events</h4>
                  <p className="text-muted-foreground">
                    Earn points for every event you attend
                  </p>
                </div>
                <div className="p-3 bg-white/50 dark:bg-black/20 rounded-lg">
                  <h4 className="font-medium mb-1">
                    Longer Events = More Points
                  </h4>
                  <p className="text-muted-foreground">
                    Events over 3 hours earn up to 2.5x points
                  </p>
                </div>
                <div className="p-3 bg-white/50 dark:bg-black/20 rounded-lg">
                  <h4 className="font-medium mb-1">Special Events</h4>
                  <p className="text-muted-foreground">
                    Workshops and conferences earn bonus points
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Leaderboard;
