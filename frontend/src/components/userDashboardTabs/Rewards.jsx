import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { useSelector } from "react-redux";
import axios from "axios";
import {
  Trophy,
  Star,
  Award,
  TrendingUp,
  Users,
  Calendar,
  History,
  RefreshCw,
  Crown,
  Medal,
  ArrowUpCircle,
  ArrowDownCircle,
  Clock,
  Flame,
  Zap,
  AlertCircle,
  Lightbulb,
  MapPin,
  Ticket,
  ArrowRight,
  CircleDollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { baseUrl } from "@/routes";
import { toast } from "sonner";
import StreakDisplay, {
  StreakMultiplierTiers,
} from "@/components/rewards/StreakDisplay";

const Rewards = ({ isActive = false }) => {
  const MIN_REDEMPTION_POINTS = 70;
  const POINTS_TO_CURRENCY_RATE = 0.01;
  const MAX_DISCOUNT_PERCENTAGE = 50;
  const { user } = useSelector((state) => state.auth);
  const [profile, setProfile] = useState(null);
  const [badges, setBadges] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [myRank, setMyRank] = useState(null);
  const [streak, setStreak] = useState(null);
  const [streakMultipliers, setStreakMultipliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);
  const [leaderboardError, setLeaderboardError] = useState(null);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [streakLoading, setStreakLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [leaderboardPeriod, setLeaderboardPeriod] = useState("all_time");
  const [showRecommendationPopup, setShowRecommendationPopup] = useState(false);
  const [popupRecommendations, setPopupRecommendations] = useState([]);
  const [popupLoading, setPopupLoading] = useState(false);
  const popupTriggeredForActivationRef = useRef(false);

  const getAuthHeaders = () => {
    const token = user?.access_token || user?.user?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${baseUrl}rewards/profile`, {
        headers: getAuthHeaders(),
      });
      setProfile(response.data);
    } catch (err) {
      console.error("Error fetching profile:", err);
      setError(err.response?.data?.detail || err.message);
    }
  };

  const fetchBadges = async () => {
    try {
      const response = await axios.get(`${baseUrl}rewards/badges`, {
        headers: getAuthHeaders(),
      });
      setBadges(response.data.badges || []);
    } catch (err) {
      console.error("Error fetching badges:", err);
    }
  };

  const fetchLeaderboard = async (period = "all_time") => {
    setLeaderboardLoading(true);
    setLeaderboardError(null);
    try {
      const response = await axios.get(`${baseUrl}rewards/leaderboard`, {
        headers: getAuthHeaders(),
        params: { period, page: 1, page_size: 50 },
      });
      setLeaderboard(response.data.entries || []);
    } catch (err) {
      console.error("Error fetching leaderboard:", err);
      const errorMessage =
        err.response?.data?.detail || "Failed to load leaderboard";
      setLeaderboardError(errorMessage);
      toast.error("Failed to load leaderboard", {
        description: errorMessage,
        action: {
          label: "Retry",
          onClick: () => fetchLeaderboard(period),
        },
      });
    } finally {
      setLeaderboardLoading(false);
    }
  };

  const fetchTransactions = async () => {
    setTransactionsLoading(true);
    try {
      const response = await axios.get(`${baseUrl}rewards/transactions`, {
        headers: getAuthHeaders(),
        params: { page: 1, page_size: 20 },
      });
      setTransactions(response.data.transactions || []);
    } catch (err) {
      console.error("Error fetching transactions:", err);
    } finally {
      setTransactionsLoading(false);
    }
  };

  const fetchMyRank = async () => {
    try {
      const response = await axios.get(
        `${baseUrl}rewards/leaderboard/my-rank`,
        {
          headers: getAuthHeaders(),
        },
      );
      setMyRank(response.data);
    } catch (err) {
      console.error("Error fetching rank:", err);
    }
  };

  const fetchStreak = async () => {
    setStreakLoading(true);
    try {
      const response = await axios.get(`${baseUrl}rewards/streak`, {
        headers: getAuthHeaders(),
      });
      setStreak(response.data);
    } catch (err) {
      console.error("Error fetching streak:", err);
    } finally {
      setStreakLoading(false);
    }
  };

  const fetchStreakMultipliers = async () => {
    try {
      const response = await axios.get(`${baseUrl}rewards/streak/multipliers`, {
        headers: getAuthHeaders(),
      });
      setStreakMultipliers(response.data.multipliers || []);
    } catch (err) {
      console.error("Error fetching streak multipliers:", err);
    }
  };

  const parseEventItems = (payload) => {
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.data?.items)) return payload.data.items;
    if (Array.isArray(payload?.items)) return payload.items;
    if (Array.isArray(payload?.data)) return payload.data;
    return [];
  };

  const parseRecommendationItems = (payload) => {
    const items = Array.isArray(payload?.recommendations)
      ? payload.recommendations
      : [];

    return items.slice(0, 3).map((item) => ({
      event_id: item.event_id,
      title: item.title,
      location: item.location,
      start_date: item.start_date,
      start_time: item.start_time,
      category: item.category,
      currency: item.currency || "EUR",
      min_ticket_price:
        typeof item.min_ticket_price === "number"
          ? item.min_ticket_price
          : null,
      potential_discount:
        typeof item.potential_discount === "number"
          ? item.potential_discount
          : 0,
      estimated_final_price:
        typeof item.estimated_final_price === "number"
          ? item.estimated_final_price
          : null,
      points_to_use: item.points_to_use || 0,
      recommendation_score: item.recommendation_score || 0,
      reasons: Array.isArray(item.reasons) ? item.reasons : [],
      source: "recommendation_api",
    }));
  };

  const parseTicketTypes = (payload) => {
    const data = payload?.data?.data || payload?.data || payload || [];
    return Array.isArray(data) ? data : [];
  };

  const calculateRedemptionPreview = (price, points) => {
    if (typeof price !== "number" || Number.isNaN(price)) {
      return {
        potential_discount: null,
        estimated_final_price: null,
        points_to_use: 0,
      };
    }

    if (points < MIN_REDEMPTION_POINTS) {
      return {
        potential_discount: 0,
        estimated_final_price: Number(price.toFixed(2)),
        points_to_use: 0,
      };
    }

    const rawDiscount = points * POINTS_TO_CURRENCY_RATE;
    const maxAllowedDiscount = price * (MAX_DISCOUNT_PERCENTAGE / 100);
    const discount = Number(
      Math.min(rawDiscount, maxAllowedDiscount).toFixed(2),
    );
    const finalPrice = Number(Math.max(price - discount, 0).toFixed(2));
    const pointsToUse = Math.max(
      0,
      Math.floor(discount / POINTS_TO_CURRENCY_RATE),
    );

    return {
      potential_discount: discount,
      estimated_final_price: finalPrice,
      points_to_use: pointsToUse,
    };
  };

  const fetchTicketPricingMap = async (eventIds) => {
    const uniqueEventIds = Array.from(new Set(eventIds.filter(Boolean)));
    if (!uniqueEventIds.length) return {};

    const pricingEntries = await Promise.all(
      uniqueEventIds.map(async (eventId) => {
        try {
          const response = await axios.get(
            `${baseUrl}events/${eventId}/ticket-types`,
          );
          const ticketTypes = parseTicketTypes(response);
          const pricedTypes = ticketTypes
            .map((ticketType) => ({
              price: Number(ticketType?.price),
              currency: ticketType?.currency || "EUR",
            }))
            .filter((ticketType) => Number.isFinite(ticketType.price));

          if (!pricedTypes.length) {
            return [eventId, null];
          }

          const cheapest = pricedTypes.reduce((acc, current) =>
            current.price < acc.price ? current : acc,
          );

          return [
            eventId,
            {
              min_ticket_price: Number(cheapest.price.toFixed(2)),
              currency: cheapest.currency,
            },
          ];
        } catch {
          return [eventId, null];
        }
      }),
    );

    return Object.fromEntries(pricingEntries);
  };

  const buildPopupRecommendations = (events, pricingMap = {}) => {
    const now = new Date();
    const currentPoints = profile?.current_points || 0;

    const toEventDateTime = (event) => {
      if (!event?.start_date) return null;

      const datePart = String(event.start_date).slice(0, 10);
      const timePart = event.start_time
        ? String(event.start_time).slice(0, 8)
        : "23:59:59";
      const parsed = new Date(`${datePart}T${timePart}`);

      if (!Number.isNaN(parsed.getTime())) return parsed;

      const fallback = new Date(event.start_date);
      return Number.isNaN(fallback.getTime()) ? null : fallback;
    };

    const enriched = events
      .map((event) => ({
        event,
        eventDateTime: toEventDateTime(event),
      }))
      .filter((item) => item.eventDateTime);

    const upcoming = enriched
      .filter((item) => item.eventDateTime >= now)
      .sort((a, b) => a.eventDateTime - b.eventDateTime)
      .map((item) => item.event);

    if (upcoming.length > 0) {
      return upcoming.slice(0, 3).map((event) => {
        const pricing = pricingMap[event.id] || null;
        const price = pricing?.min_ticket_price;
        const redemption = calculateRedemptionPreview(price, currentPoints);

        return {
          event_id: event.id,
          title: event.title,
          location: event.location,
          start_date: event.start_date,
          start_time: event.start_time,
          category: event?.category?.name || "General",
          currency: pricing?.currency || "EUR",
          min_ticket_price: typeof price === "number" ? price : null,
          potential_discount: redemption.potential_discount,
          estimated_final_price: redemption.estimated_final_price,
          points_to_use: redemption.points_to_use,
          recommendation_score: 0,
          reasons: [],
          source: "events_fallback",
        };
      });
    }

    return [];
  };

  const fetchPopupRecommendations = async () => {
    setPopupLoading(true);
    let resolvedRecommendations = [];
    try {
      const recommendationResponse = await axios.get(
        `${baseUrl}rewards/recommendations/next-events`,
        {
          headers: getAuthHeaders(),
          params: { limit: 3 },
        },
      );

      const recommendationItems = parseRecommendationItems(
        recommendationResponse.data,
      );

      if (recommendationItems.length > 0) {
        resolvedRecommendations = recommendationItems;
      } else {
        const eventsResponse = await axios.get(`${baseUrl}events/`, {
          params: { time_filter: "upcoming", page_size: 50 },
        });
        const events = parseEventItems(eventsResponse.data);
        const baseRecommendations = buildPopupRecommendations(events);
        const pricingMap = await fetchTicketPricingMap(
          baseRecommendations.map((item) => item.event_id),
        );
        resolvedRecommendations = buildPopupRecommendations(events, pricingMap);
      }
    } catch (err) {
      console.error("Error fetching popup recommendations:", err);
      try {
        const eventsResponse = await axios.get(`${baseUrl}events/`, {
          params: { time_filter: "upcoming", page_size: 50 },
        });
        const events = parseEventItems(eventsResponse.data);
        const baseRecommendations = buildPopupRecommendations(events);
        const pricingMap = await fetchTicketPricingMap(
          baseRecommendations.map((item) => item.event_id),
        );
        resolvedRecommendations = buildPopupRecommendations(events, pricingMap);
      } catch (fallbackError) {
        console.error("Fallback event fetch failed:", fallbackError);
        resolvedRecommendations = [];
      }
    } finally {
      setPopupRecommendations(resolvedRecommendations);
      setPopupLoading(false);
    }

    return resolvedRecommendations;
  };

  useEffect(() => {
    const initializeData = async () => {
      if (!user) return;

      setLoading(true);
      await Promise.all([
        fetchProfile(),
        fetchBadges(),
        fetchMyRank(),
        fetchStreak(),
        fetchStreakMultipliers(),
      ]);
      setLoading(false);
    };

    initializeData();
  }, [user]);

  useEffect(() => {
    if (!isActive) {
      popupTriggeredForActivationRef.current = false;
      setShowRecommendationPopup(false);
      return;
    }

    const currentPoints = profile?.current_points || 0;
    if (currentPoints < MIN_REDEMPTION_POINTS) {
      setShowRecommendationPopup(false);
      return;
    }

    if (!popupTriggeredForActivationRef.current) {
      popupTriggeredForActivationRef.current = true;
      (async () => {
        const recommendations = await fetchPopupRecommendations();
        setShowRecommendationPopup(recommendations.length > 0);
      })();
    }
  }, [isActive, profile?.current_points]);

  useEffect(() => {
    if (activeTab === "leaderboard") {
      fetchLeaderboard(leaderboardPeriod);
    } else if (activeTab === "history") {
      fetchTransactions();
    } else if (activeTab === "streak") {
      fetchStreak();
    }
  }, [activeTab, leaderboardPeriod]);

  const handleRefresh = () => {
    fetchProfile();
    fetchStreak();
    if (activeTab === "leaderboard") {
      fetchLeaderboard(leaderboardPeriod);
    } else if (activeTab === "history") {
      fetchTransactions();
    } else if (activeTab === "streak") {
      fetchStreak();
    }
  };

  const handleLeaderboardPeriodChange = (period) => {
    setLeaderboardPeriod(period);
    fetchLeaderboard(period);
  };

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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatMoney = (amount, currency = "EUR") => {
    if (typeof amount !== "number") return null;
    return `${currency} ${amount.toFixed(2)}`;
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getReasonDisplay = (reason) => {
    const reasonMap = {
      event_attendance: "Event Attendance",
      redemption_discount: "Points Redeemed",
      bonus: "Bonus Points",
      referral: "Referral Bonus",
      adjustment: "Admin Adjustment",
    };
    return reasonMap[reason] || reason;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <h2 className="text-xl font-bold text-red-600 mb-4">
            Error Loading Rewards
          </h2>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  const estimatedDiscountEuro = ((profile?.current_points || 0) * 0.01).toFixed(
    2,
  );

  return (
    <div className="space-y-6">
      <Dialog
        open={showRecommendationPopup}
        onOpenChange={setShowRecommendationPopup}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-amber-500" />
              Recommended Next Tickets
            </DialogTitle>
            <DialogDescription>
              You currently have {profile?.current_points || 0} points and can
              redeem up to EUR {estimatedDiscountEuro} discount on your next
              ticket purchase (subject to event redemption limits).
            </DialogDescription>
          </DialogHeader>

          {popupLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : popupRecommendations.length === 0 ? (
            <div className="rounded-lg border bg-muted/30 p-4 text-sm text-muted-foreground">
              We are preparing recommendations for you. Please explore events
              and this popup will auto-suggest 1-3 tickets next time.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {popupRecommendations.map((event) => (
                <div
                  key={event.event_id}
                  className="rounded-lg border p-4 bg-gradient-to-r from-primary/5 to-secondary/5"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="font-semibold text-base">
                          {event.title}
                        </h4>
                        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            <span>{formatDate(event.start_date)}</span>
                          </div>
                          {event.location && (
                            <div className="flex items-center gap-2">
                              <MapPin className="w-4 h-4" />
                              <span>{event.location}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-right space-y-2">
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          <Ticket className="w-3 h-3" />
                          Suggested
                        </span>
                        {event.potential_discount > 0 && (
                          <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                            Save{" "}
                            {formatMoney(
                              event.potential_discount,
                              event.currency,
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-md border border-primary/20 bg-white/60 dark:bg-background/40 p-3">
                      {typeof event.min_ticket_price === "number" &&
                      typeof event.estimated_final_price === "number" ? (
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                          <div>
                            <p className="text-muted-foreground">
                              Ticket Price
                            </p>
                            <p className="font-semibold">
                              {formatMoney(
                                event.min_ticket_price,
                                event.currency,
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Discount</p>
                            <p className="font-semibold text-emerald-600 dark:text-emerald-400">
                              -
                              {formatMoney(
                                event.potential_discount || 0,
                                event.currency,
                              )}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Pay Now</p>
                            <p className="font-bold text-primary">
                              {formatMoney(
                                event.estimated_final_price,
                                event.currency,
                              )}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <CircleDollarSign className="w-4 h-4" />
                            <span>
                              Redeem points at checkout to unlock your best
                              price.
                            </span>
                          </div>
                        </div>
                      )}

                      {event.points_to_use > 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Uses {event.points_to_use} points for this deal.
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end">
                      <Link to={`/events/${event.event_id}`}>
                        <Button size="sm" className="group">
                          View Event & Buy
                          <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Trophy className="w-6 h-6 text-primary" />
            Rewards Center
          </h2>
          <p className="text-muted-foreground mt-1">
            Earn points, unlock badges, and track your achievements
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      {/* stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Available Points
                </p>
                <p className="text-3xl font-bold text-primary">
                  {profile?.current_points?.toLocaleString() || 0}
                </p>
              </div>
              <Star className="w-10 h-10 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Lifetime Points</p>
                <p className="text-3xl font-bold">
                  {profile?.lifetime_points?.toLocaleString() || 0}
                </p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Events Attended</p>
                <p className="text-3xl font-bold">
                  {profile?.total_events_joined || 0}
                </p>
              </div>
              <Calendar className="w-10 h-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        {/* Streak Card */}
        <Card
          className={cn(
            streak?.current_streak > 0 &&
              "border-orange-200 dark:border-orange-800",
          )}
        >
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Current Streak</p>
                <div className="flex items-center gap-2">
                  <p
                    className={cn(
                      "text-3xl font-bold",
                      streak?.current_streak > 0 ? "text-orange-500" : "",
                    )}
                  >
                    {streak?.current_streak || 0}
                  </p>
                  {streak?.streak_multiplier > 1 && (
                    <span className="text-sm text-yellow-600 dark:text-yellow-400 font-medium">
                      ({streak.streak_multiplier}x)
                    </span>
                  )}
                </div>
              </div>
              <Flame
                className={cn(
                  "w-10 h-10",
                  streak?.current_streak > 0
                    ? "text-orange-500"
                    : "text-gray-400",
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Your Rank</p>
                <p className="text-3xl font-bold">
                  {myRank?.rank ? `#${myRank.rank}` : "—"}
                </p>
              </div>
              <Users className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* main tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="streak" className="flex items-center gap-2">
            <Flame className="w-4 h-4" />
            <span className="hidden sm:inline">Streak</span>
          </TabsTrigger>
          <TabsTrigger value="badges" className="flex items-center gap-2">
            <Star className="w-4 h-4" />
            <span className="hidden sm:inline">Badges</span>
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="flex items-center gap-2">
            <Trophy className="w-4 h-4" />
            <span className="hidden sm:inline">Leaderboard</span>
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="w-4 h-4" />
            <span className="hidden sm:inline">History</span>
          </TabsTrigger>
        </TabsList>

        {/* overview tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* current badge */}
            <Card>
              <CardHeader>
                <CardTitle>Your Badge</CardTitle>
                <CardDescription>
                  Your current achievement level
                </CardDescription>
              </CardHeader>
              <CardContent>
                {profile?.current_level ? (
                  <div className="flex flex-col items-center text-center">
                    <div
                      className="w-20 h-20 rounded-full flex items-center justify-center mb-3 shadow-lg transition-transform hover:scale-105"
                      style={{
                        background: `linear-gradient(135deg, ${profile.current_level.badge_color}40, ${profile.current_level.badge_color})`,
                        border: `3px solid ${profile.current_level.badge_color}`,
                      }}
                    >
                      <Star
                        className="w-10 h-10 text-white drop-shadow-md"
                        fill="currentColor"
                      />
                    </div>
                    <h3
                      className="font-bold text-lg"
                      style={{ color: profile.current_level.badge_color }}
                    >
                      {profile.current_level.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                      {profile.current_level.description}
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center p-4 text-center">
                    <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-2">
                      <Award className="w-8 h-8 text-gray-400" />
                    </div>
                    <span className="text-sm text-muted-foreground">
                      No badge yet
                    </span>
                    <span className="text-xs text-muted-foreground mt-1">
                      Earn 500 points to get your first badge!
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* progress to next badge */}
            <Card>
              <CardHeader>
                <CardTitle>Progress</CardTitle>
                <CardDescription>
                  Your journey to the next level
                </CardDescription>
              </CardHeader>
              <CardContent>
                {profile?.next_level ? (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Progress to {profile.next_level.name}
                      </span>
                      <span className="font-medium">
                        {profile.lifetime_points} /{" "}
                        {profile.next_level.min_points}
                      </span>
                    </div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(
                            (profile.lifetime_points /
                              profile.next_level.min_points) *
                              100,
                            100,
                          )}%`,
                          backgroundColor: profile.next_level.badge_color,
                        }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground text-center">
                      {profile.points_to_next_level} points to go!
                    </p>
                  </div>
                ) : (
                  <div className="text-center p-4 bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 rounded-lg">
                    <span className="text-amber-600 dark:text-amber-400 font-medium">
                      🎉 Maximum level achieved!
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* how to earn points */}
          <Card>
            <CardHeader>
              <CardTitle>How to Earn Points</CardTitle>
              <CardDescription>
                Participate in events to earn reward points
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2">Attend Events</h4>
                  <p className="text-sm text-muted-foreground">
                    Earn 10-30+ points per event based on duration and type
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2">Workshop Bonus</h4>
                  <p className="text-sm text-muted-foreground">
                    Workshops and conferences earn 2x points
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2">Exclusive Events</h4>
                  <p className="text-sm text-muted-foreground">
                    Smaller events (&lt;20 capacity) earn bonus points
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* streak tab */}
        <TabsContent value="streak" className="space-y-6">
          <StreakDisplay streak={streak} loading={streakLoading} />
          <StreakMultiplierTiers
            multipliers={streakMultipliers}
            currentStreak={streak?.current_streak || 0}
          />

          {/* How streaks work */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                How Streaks Work
              </CardTitle>
              <CardDescription>
                Build your streak to earn bonus points on every purchase
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-5 h-5 text-blue-500" />
                    <h4 className="font-medium">Weekly Activity</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Attend at least one event each week to maintain your streak
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    <h4 className="font-medium">Growing Multiplier</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Longer streaks unlock higher point multipliers, up to 2x!
                  </p>
                </div>
                <div className="p-4 bg-muted/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Flame className="w-5 h-5 text-orange-500" />
                    <h4 className="font-medium">Keep It Going</h4>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Missing a week resets your streak - stay active to maximize
                    rewards!
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* badges tab */}
        <TabsContent value="badges">
          <Card>
            <CardHeader>
              <CardTitle>All Badges</CardTitle>
              <CardDescription>
                Earn points to unlock these achievement badges
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {badges.map((badge) => {
                  const isUnlocked =
                    profile?.lifetime_points >= badge.min_points;
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* leaderboard tab */}
        <TabsContent value="leaderboard">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <CardTitle>Leaderboard</CardTitle>
                  <CardDescription>
                    Top performers in our community
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {["all_time", "weekly", "monthly"].map((period) => (
                    <Button
                      key={period}
                      variant={
                        leaderboardPeriod === period ? "default" : "outline"
                      }
                      size="sm"
                      onClick={() => handleLeaderboardPeriodChange(period)}
                    >
                      {period === "all_time"
                        ? "All Time"
                        : period.charAt(0).toUpperCase() + period.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {leaderboardLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : leaderboardError ? (
                <div className="text-center py-12 space-y-4">
                  <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
                  <div>
                    <p className="text-red-600 dark:text-red-400 font-medium mb-2">
                      Failed to load leaderboard
                    </p>
                    <p className="text-sm text-muted-foreground mb-4">
                      {leaderboardError}
                    </p>
                    <Button
                      onClick={() => fetchLeaderboard(leaderboardPeriod)}
                      variant="outline"
                      size="sm"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Try Again
                    </Button>
                  </div>
                </div>
              ) : leaderboard.length === 0 ? (
                <div className="text-center py-12">
                  <Trophy className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    No entries yet. Be the first!
                  </p>
                </div>
              ) : (
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
                      {leaderboard.map((entry) => {
                        const isCurrentUser =
                          entry.user_id === (user?.user?.id || user?.id);
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
                                <span className="text-muted-foreground text-xs">
                                  —
                                </span>
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
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* history tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Point History</CardTitle>
              <CardDescription>
                Your complete transaction history
              </CardDescription>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : transactions.length === 0 ? (
                <div className="text-center py-12">
                  <Clock className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No transactions yet</p>
                </div>
              ) : (
                <div className="overflow-hidden rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead className="w-12"></TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-center">Date</TableHead>
                        <TableHead className="text-right">Points</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {transactions.map((transaction) => {
                        const isPositive = transaction.points_delta > 0;
                        return (
                          <TableRow
                            key={transaction.id}
                            className="hover:bg-muted/30"
                          >
                            <TableCell>
                              {isPositive ? (
                                <ArrowUpCircle className="w-5 h-5 text-green-500" />
                              ) : (
                                <ArrowDownCircle className="w-5 h-5 text-red-500" />
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-col">
                                <span className="font-medium">
                                  {transaction.description ||
                                    getReasonDisplay(transaction.reason)}
                                </span>
                                {transaction.event_id && (
                                  <span className="text-xs text-muted-foreground">
                                    Event ID: {transaction.event_id.slice(0, 8)}
                                    ...
                                  </span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <span
                                className={cn(
                                  "px-2 py-1 rounded-full text-xs font-medium",
                                  isPositive
                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                                )}
                              >
                                {getReasonDisplay(transaction.reason)}
                              </span>
                            </TableCell>
                            <TableCell className="text-center">
                              <div className="flex flex-col items-center">
                                <span className="text-sm">
                                  {formatDate(transaction.created_at)}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {formatTime(transaction.created_at)}
                                </span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <span
                                className={cn(
                                  "font-bold text-lg",
                                  isPositive
                                    ? "text-green-600 dark:text-green-400"
                                    : "text-red-600 dark:text-red-400",
                                )}
                              >
                                {isPositive ? "+" : ""}
                                {transaction.points_delta.toLocaleString()}
                              </span>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Rewards;
