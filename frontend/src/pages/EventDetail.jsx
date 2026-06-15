import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import axios from "axios";
import { baseUrl } from "../routes";
import {
  Bookmark,
  MapPin,
  Calendar,
  Clock,
  Users,
  MessageSquare,
  Tag,
  ArrowLeft,
  ExternalLink,
  Gift,
  Coins,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import { useSelector, useDispatch } from "react-redux";
import socketService from "@/services/socketService";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { fetchMyProfile } from "@/store/slices/rewardSlice";
import TicketPurchaseModal from "../components/events/TicketPurchaseModal";
import userApiService from "@/services/userApiService";

const EventDetail = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ticketTypes, setTicketTypes] = useState([]);
  const [loadingTicketTypes, setLoadingTicketTypes] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [purchasedTicketId, setPurchasedTicketId] = useState(null);
  const { isAuthenticated, user } = useSelector((state) => state.auth);
  const { profile: rewardProfile } = useSelector((state) => state.rewards);

  // Purchase Modal State
  const [isTicketDialogOpen, setIsTicketDialogOpen] = useState(false);
  const [cart, setCart] = useState({}); // { ticket_id: { ticket, quantity } }
  const [isPurchaseConfirmOpen, setIsPurchaseConfirmOpen] = useState(false);
  const [redeemPoints, setRedeemPoints] = useState("");
  const [isPurchasing, setIsPurchasing] = useState(false);

  // Image Carousel State
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const openGallery = () => {
    setCurrentImageIndex(0);
    setIsGalleryOpen(true);
  };

  const nextImage = () => {
    if (event?.images) {
      setCurrentImageIndex((prev) => (prev + 1) % event.images.length);
    }
  };

  const prevImage = () => {
    if (event?.images) {
      setCurrentImageIndex(
        (prev) => (prev - 1 + event.images.length) % event.images.length,
      );
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isGalleryOpen) return;

      if (e.key === "ArrowLeft") {
        prevImage();
      } else if (e.key === "ArrowRight") {
        nextImage();
      } else if (e.key === "Escape") {
        setIsGalleryOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isGalleryOpen, event]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`${baseUrl}events/${id}`);
        setEvent(res.data?.data);
      } catch (err) {
        console.error("Failed to load event:", err);
        setError("Failed to load event");
      } finally {
        setLoading(false);
      }
    };

    load();
    loadTicketTypes();
  }, [id]);

  // Fetch reward profile when dialog opens
  useEffect(() => {
    if (isTicketDialogOpen && isAuthenticated) {
      dispatch(fetchMyProfile());
    }
  }, [isTicketDialogOpen, isAuthenticated, dispatch]);

  const loadTicketTypes = async () => {
    try {
      setLoadingTicketTypes(true);
      const headers = {};
      if (user?.access_token) {
        headers.Authorization = `Bearer ${user.access_token}`;
      }
      const res = await axios.get(`${baseUrl}events/${id}/ticket-types`, {
        headers,
      });
      const data = res.data?.data || res.data || [];
      setTicketTypes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load ticket types:", err);
      setTicketTypes([]);
    } finally {
      setLoadingTicketTypes(false);
    }
  };

  const handleProceedToCheckout = () => {
    setRedeemPoints("");
    setIsTicketDialogOpen(false);
    setIsPurchaseConfirmOpen(true);
  };

  const handleUpdateCart = (ticket, newQuantity) => {
    if (newQuantity < 0) return;
    setCart((prev) => {
      const updated = { ...prev };
      if (newQuantity === 0) {
        delete updated[ticket.id];
      } else {
        updated[ticket.id] = { ticket, quantity: newQuantity };
      }
      return updated;
    });
  };

  const getCartTotal = () => {
    return Object.values(cart).reduce(
      (sum, item) => sum + item.ticket.price * item.quantity,
      0,
    );
  };

  const handleConfirmPurchase = async () => {
    if (Object.keys(cart).length === 0) return;

    const pointsToRedeem = parseInt(redeemPoints, 10) || 0;
    const availablePoints = rewardProfile?.current_points || 0;

    if (pointsToRedeem > availablePoints) {
      toast.error("Insufficient reward points", {
        description: `You can redeem up to ${availablePoints} points.`,
      });
      return;
    }

    if (pointsToRedeem > 0 && pointsToRedeem < 100) {
      toast.error("Minimum redemption is 100 points");
      return;
    }

    setIsPurchasing(true);
    try {
      const headers = {};
      if (user?.access_token) {
        headers.Authorization = `Bearer ${user.access_token}`;
      }

      const items = Object.values(cart).map((item) => ({
        ticket_type_id: item.ticket.id,
        quantity: item.quantity,
      }));

      const response = await axios.post(
        `${baseUrl}tickets/purchase`,
        {
          event_id: id,
          items: items,
          redeem_points: pointsToRedeem > 0 ? pointsToRedeem : null,
        },
        { headers },
      );

      const result = response.data?.data || response.data;
      setIsTicketDialogOpen(false);

      const newTicketId = result?.ticket_id || response.data?.ticket_id;
      if (newTicketId) {
        setPurchasedTicketId(newTicketId);
        setShowSuccessModal(true);
      }

      setIsPurchaseConfirmOpen(false);
      // Wait to clear cart until success modal closes so it can be used for PDF

      // Build success message
      let successMessage = "Ticket purchase successful!";
      let description = "You've been added to the event group chat.";

      if (result?.points_awarded > 0) {
        description = `You earned ${result.points_awarded} points! `;
        if (result.badge_upgraded && result.new_badge_name) {
          description += `🎉 You've earned the ${result.new_badge_name} badge!`;
        }
      }

      if (result?.points_redeemed > 0) {
        description += ` Discount of €${result.discount_applied?.toFixed(
          2,
        )} applied.`;
      }

      toast.success(successMessage, { description });

      // Refresh reward profile
      dispatch(fetchMyProfile());
    } catch (err) {
      console.error("Purchase failed:", err);
      toast.error("Failed to buy ticket", {
        description:
          err.response?.data?.message ||
          err.response?.data?.detail ||
          err.message,
      });
    } finally {
      setIsPurchasing(false);
    }
  };

  const calculateDiscount = () => {
    const points = parseInt(redeemPoints, 10) || 0;
    if (Object.keys(cart).length === 0 || points === 0) return 0;

    // 1 point = €0.01
    const rawDiscount = points * 0.01;
    const totalPrice = getCartTotal();

    // Apply max discount cap (50% of total price)
    const maxDiscountPercentage = 50;
    const maxDiscount = totalPrice * (maxDiscountPercentage / 100);

    return Math.min(rawDiscount, maxDiscount).toFixed(2);
  };

  const isDiscountCapped = () => {
    const points = parseInt(redeemPoints, 10) || 0;
    if (Object.keys(cart).length === 0 || points === 0) return false;

    const rawDiscount = points * 0.01;
    const totalPrice = getCartTotal();
    const maxDiscount = totalPrice * 0.5;
    return rawDiscount > maxDiscount;
  };

  const calculateFinalPrice = () => {
    const totalPrice = getCartTotal();
    if (!totalPrice) return "0.00";
    const discount = calculateDiscount();
    return Math.max(0, totalPrice - discount).toFixed(2);
  };

  const parsedRedeemPoints = parseInt(redeemPoints, 10) || 0;
  const availableRewardPoints = rewardProfile?.current_points || 0;
  const redeemExceedsBalance = parsedRedeemPoints > availableRewardPoints;

  // Bookmark state
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [loadingBookmark, setLoadingBookmark] = useState(false);

  useEffect(() => {
    const checkBookmark = async () => {
      if (isAuthenticated && user?.user?.id && id) {
        try {
          const status = await userApiService.checkBookmarkStatus(
            user.user.id,
            id,
          );
          setIsBookmarked(status.is_bookmarked);
        } catch (err) {
          console.error("Failed to check bookmark status", err);
        }
      }
    };
    checkBookmark();
  }, [id, isAuthenticated, user]);

  const handleToggleBookmark = async () => {
    if (!isAuthenticated) {
      toast.error("Please login to bookmark events");
      return;
    }

    try {
      setLoadingBookmark(true);
      if (isBookmarked) {
        await userApiService.removeBookmark(user.user.id, id);
        setIsBookmarked(false);
        toast.success("Bookmark removed");
      } else {
        await userApiService.addBookmark(user.user.id, id);
        setIsBookmarked(true);
        toast.success("Event bookmarked");
      }
    } catch (err) {
      console.error("Failed to toggle bookmark", err);
      toast.error("Failed to update bookmark");
    } finally {
      setLoadingBookmark(false);
    }
  };

  if (loading)
    return (
      <div className="min-h-screen bg-linear-to-b from-background to-muted/50 flex justify-center items-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );

  if (error || !event)
    return (
      <div className="min-h-screen bg-linear-to-b from-background to-muted/50 flex flex-col justify-center items-center gap-4">
        <p className="text-destructive text-lg">{error || "Event not found"}</p>
        <Link to="/events">
          <Button variant="outline">Back to Events</Button>
        </Link>
      </div>
    );

  const {
    title,
    description,
    images,
    category,
    location,
    latitude,
    longitude,
    start_date,
    start_time,
    end_date,
    end_time,
    organizer,
    max_attendees,
    status,
  } = event;

  const image = images && images[0];
  const hasMultipleImages = images && images.length > 1;
  const additionalImagesCount = hasMultipleImages ? images.length - 1 : 0;

  const formattedStart = `${start_date} • ${start_time}`;
  const formattedEnd = `${end_date} • ${end_time}`;

  return (
    <div className="min-h-screen bg-linear-to-b from-background to-muted/50 pb-24">
      <div className="container mx-auto px-4 py-8">
        <Link to="/events">
          <Button
            variant="outline"
            className="mb-6 hover:bg-primary/5 hover:text-primary hover:border-primary/50 transition-all duration-300"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Events
          </Button>
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div
              className={`relative h-96 rounded-xl overflow-hidden bg-muted group ${
                hasMultipleImages ? "cursor-pointer" : ""
              }`}
              onClick={hasMultipleImages ? openGallery : undefined}
            >
              <img
                src={image}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                alt={title}
              />

              {hasMultipleImages && (
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-300 flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transform translate-y-4 group-hover:translate-y-0 transition-all duration-300 bg-black/60 backdrop-blur-sm text-white px-6 py-3 rounded-full font-semibold flex items-center gap-2">
                    <span className="text-xl">+ {additionalImagesCount}</span>
                    <span>more photos</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-3xl md:text-4xl font-bold mb-3 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                  {title}
                </h1>
                <div className="flex items-center gap-3 flex-wrap">
                  {category?.name && (
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full">
                      <Tag className="w-4 h-4 text-primary" />
                      <span className="text-sm font-semibold text-primary">
                        {category.name}
                      </span>
                    </div>
                  )}
                  {status === "pending" && (
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-full border border-yellow-200 dark:border-yellow-800">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-semibold text-yellow-700 dark:text-yellow-400">
                        Pending Approval
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleToggleBookmark}
                  disabled={loadingBookmark}
                  className={`p-3 border shadow-md rounded-full hover:scale-110 transition-all cursor-pointer ${
                    isBookmarked
                      ? "bg-primary border-primary text-white"
                      : "bg-card border-border hover:border-primary/50 text-primary"
                  }`}
                >
                  <Bookmark
                    className={`w-5 h-5 ${isBookmarked ? "fill-current" : ""}`}
                  />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="border-primary/20 hover:border-primary/50 transition-all hover:shadow-lg">
                <CardContent className="pt-2">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-primary/10 rounded-xl">
                      <Calendar className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Start Date
                      </p>
                      <p className="font-semibold">{start_date}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-secondary/20 hover:border-secondary/50 transition-all hover:shadow-lg">
                <CardContent className="pt-2">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-secondary/10 rounded-xl">
                      <Clock className="w-5 h-5 text-secondary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Start Time
                      </p>
                      <p className="font-semibold">{start_time}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-accent/20 hover:border-accent/50 transition-all hover:shadow-lg">
                <CardContent className="pt-2">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-accent/10 rounded-xl">
                      <Users className="w-5 h-5 text-accent" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Max Attendees
                      </p>
                      <p className="font-semibold">{max_attendees}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-2xl">About This Event</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {description}
                </p>
              </CardContent>
            </Card>

            {ticketTypes.length > 0 && (
              <Card className="shadow-sm">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2">
                    <Tag className="w-5 h-5 text-primary" />
                    Available Ticket Types
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {ticketTypes.map((ticket) => (
                      <div
                        key={ticket.id}
                        className="p-4 border rounded-lg hover:border-primary/50 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h4 className="font-semibold text-lg">
                              {ticket.name}
                            </h4>
                            {ticket.description && (
                              <p className="text-sm text-muted-foreground mt-1">
                                {ticket.description}
                              </p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-primary">
                              {new Intl.NumberFormat("en-US", {
                                style: "currency",
                                currency: ticket.currency || "USD",
                              }).format(ticket.price)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span>Capacity: {ticket.capacity}</span>
                          {ticket.max_per_user && (
                            <span>Max per user: {ticket.max_per_user}</span>
                          )}
                          {ticket.resale_allowed && (
                            <span className="text-green-600 dark:text-green-400">
                              ✓ Resale allowed
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-xl flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-primary" />
                  Event Schedule
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-around p-4 bg-muted/50 rounded-xl">
                  <div>
                    <p className="text-sm text-muted-foreground">Starts</p>
                    <p className="font-semibold">{formattedStart}</p>
                  </div>
                  <div className="h-8 w-px bg-border"></div>
                  <div>
                    <p className="text-sm text-muted-foreground">Ends</p>
                    <p className="font-semibold">{formattedEnd}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <aside className="lg:col-span-1 space-y-6 lg:sticky lg:top-32 h-fit">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-primary" />
                  Location
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted/50 rounded-xl">
                  <p className="font-medium text-foreground">{location}</p>
                </div>

                {/* Map component */}
                <div className="relative h-64 rounded-xl overflow-hidden border border-border">
                  <iframe
                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${
                      longitude - 0.01
                    },${latitude - 0.01},${longitude + 0.01},${
                      latitude + 0.01
                    }&layer=mapnik&marker=${latitude},${longitude}`}
                    className="w-full h-full border-0"
                    title="Event Location Map"
                  />
                </div>

                <div className="space-y-2">
                  <a
                    href={`https://www.google.com/maps?q=${latitude},${longitude}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Button className="w-full shadow-md hover:shadow-lg cursor-pointer transition-all">
                      <MapPin className="w-4 h-4 mr-2" />
                      Open in Google Maps
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">Organized By</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-linear-to-br from-primary to-secondary rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                    {organizer?.name?.[0]?.toUpperCase() || "?"}
                  </div>
                  <div>
                    <p className="font-semibold">
                      {organizer?.name || "Unknown Organizer"}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Event Organizer
                    </p>
                  </div>
                </div>

                {isAuthenticated && user?.user?.id !== organizer?.id && (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      socketService.joinDirect(organizer.id, event.id);
                    }}
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Contact Organizer
                  </Button>
                )}
              </CardContent>
            </Card>

            {isAuthenticated && user?.user?.id === organizer?.id ? (
              <Link to={`/events/${id}/ticket-types`}>
                <Button
                  size="lg"
                  className="w-full shadow-xl hover:shadow-2xl hover:scale-102 transition-all duration-300 text-lg py-6"
                >
                  <Tag className="w-5 h-5 mr-2" />
                  Manage Ticket Types
                </Button>
              </Link>
            ) : (
              <Button
                onClick={() => {
                  if (isAuthenticated) {
                    setIsTicketDialogOpen(true);
                  } else {
                    toast.error("Please login to purchase tickets");
                  }
                }}
                disabled={(() => {
                  const now = new Date();
                  const eventEnd = new Date(
                    `${event.end_date}T${event.end_time}`,
                  );
                  const isEventOver = now > eventEnd;
                  const isEventCancelled = event.status !== "approved";

                  const isBookingClosed =
                    ticketTypes.length > 0 &&
                    ticketTypes.every((ticket) => {
                      if (!ticket.sale_ends_at) return false;
                      return new Date(ticket.sale_ends_at) < now;
                    });

                  return isEventOver || isEventCancelled || isBookingClosed;
                })()}
                size="lg"
                className="w-full shadow-xl hover:shadow-2xl hover:scale-102 transition-all duration-300 text-lg py-6 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {(() => {
                  const now = new Date();
                  const eventEnd = new Date(
                    `${event.end_date}T${event.end_time}`,
                  );
                  const isEventOver = now > eventEnd;
                  const isEventWaitingfroApproval = event.status !== "approved";

                  const isBookingClosed =
                    ticketTypes.length > 0 &&
                    ticketTypes.every((ticket) => {
                      if (!ticket.sale_ends_at) return false;
                      return new Date(ticket.sale_ends_at) < now;
                    });

                  if (isEventWaitingfroApproval) return "Booking Soon";
                  if (isEventOver) return "Event Ended";
                  if (isBookingClosed) return "Booking Closed";
                  return "Purchase Ticket";
                })()}
              </Button>
            )}
          </aside>
        </div>
      </div>

      <Dialog open={isTicketDialogOpen} onOpenChange={setIsTicketDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Select Ticket Type</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {loadingTicketTypes ? (
              <div className="flex justify-center p-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : ticketTypes.length === 0 ? (
              <p className="text-center text-muted-foreground">
                No tickets available.
              </p>
            ) : (
              ticketTypes.map((ticket) => {
                const cartQty = cart[ticket.id]?.quantity || 0;
                return (
                  <div
                    key={ticket.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:border-primary/50 hover:bg-muted/50 transition-all group"
                  >
                    <div className="flex-1">
                      <h4 className="font-semibold">{ticket.name}</h4>
                      {ticket.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {ticket.description}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        Capacity: {ticket.capacity}
                      </p>
                    </div>
                    <div className="text-right pl-4 pr-2">
                      <p className="text-lg font-bold text-primary transition-transform mb-2">
                        {new Intl.NumberFormat("en-US", {
                          style: "currency",
                          currency: ticket.currency || "USD",
                        }).format(ticket.price)}
                      </p>
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleUpdateCart(ticket, cartQty - 1)}
                          disabled={cartQty === 0}
                        >
                          -
                        </Button>
                        <span className="w-5 text-center text-sm font-semibold">
                          {cartQty}
                        </span>
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => handleUpdateCart(ticket, cartQty + 1)}
                          disabled={
                            cartQty >=
                            Math.min(
                              ticket.max_per_user || 10,
                              ticket.capacity || 10,
                            )
                          }
                        >
                          +
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
          {Object.keys(cart).length > 0 && (
            <div className="pt-4 border-t flex justify-between items-center -mx-6 px-6 pb-2 -mb-2">
              <div>
                <p className="text-sm text-muted-foreground font-medium">
                  Cart Total
                </p>
                <p className="text-xl font-bold text-primary">
                  {new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "EUR",
                  }).format(getCartTotal())}
                </p>
              </div>
              <Button onClick={handleProceedToCheckout}>
                Proceed to Checkout
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Purchase Confirmation Dialog with Redemption */}
      <Dialog
        open={isPurchaseConfirmOpen}
        onOpenChange={setIsPurchaseConfirmOpen}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Coins className="w-5 h-5 text-primary" />
              Confirm Purchase
            </DialogTitle>
          </DialogHeader>

          {Object.keys(cart).length > 0 && (
            <div className="space-y-4 py-4">
              {/* Ticket Info */}
              <div className="bg-muted/50 p-4 rounded-lg space-y-3">
                {Object.values(cart).map((item) => (
                  <div
                    key={item.ticket.id}
                    className="flex justify-between items-start border-b border-primary/5 pb-2 last:border-0 last:pb-0"
                  >
                    <div>
                      <h4 className="font-semibold">
                        {item.quantity}x {item.ticket.name}
                      </h4>
                    </div>
                    <div>
                      <p className="font-medium text-primary">
                        {new Intl.NumberFormat("en-US", {
                          style: "currency",
                          currency: item.ticket.currency || "USD",
                        }).format(item.ticket.price * item.quantity)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Reward Points Section */}
              {isAuthenticated &&
                rewardProfile &&
                rewardProfile.current_points > 0 && (
                  <div className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Gift className="w-4 h-4 text-primary" />
                        <span className="font-medium">Use Reward Points</span>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        Available:{" "}
                        <span className="font-bold text-primary">
                          {rewardProfile.current_points}
                        </span>
                      </span>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="redeemPoints">
                        Points to Redeem (1 point = €0.01, max 50% off)
                      </Label>
                      <Input
                        id="redeemPoints"
                        type="number"
                        min="0"
                        placeholder="Enter points to redeem"
                        value={redeemPoints}
                        onChange={(e) => {
                          const input = e.target.value;

                          if (input === "") {
                            setRedeemPoints("");
                            return;
                          }

                          const numericValue = Math.max(
                            0,
                            parseInt(input, 10) || 0,
                          );
                          setRedeemPoints(numericValue.toString());
                        }}
                      />
                      {parsedRedeemPoints > 0 && parsedRedeemPoints < 100 && (
                        <p className="text-xs text-destructive">
                          Minimum redemption is 100 points
                        </p>
                      )}
                      {redeemExceedsBalance && (
                        <p className="text-xs text-destructive">
                          You cannot redeem more than your available points.
                        </p>
                      )}
                    </div>

                    {/* Quick Buttons */}
                    <div className="flex flex-wrap gap-2">
                      {[100, 250, 500]
                        .filter((amt) => amt <= rewardProfile.current_points)
                        .map((amount) => (
                          <Button
                            key={amount}
                            variant="outline"
                            size="sm"
                            onClick={() => setRedeemPoints(amount.toString())}
                            className="text-xs"
                          >
                            {amount} pts (€{(amount * 0.01).toFixed(2)})
                          </Button>
                        ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setRedeemPoints(
                            Math.min(
                              rewardProfile.current_points,
                              Math.floor(getCartTotal() * 100),
                            ).toString(),
                          )
                        }
                        className="text-xs"
                      >
                        Max
                      </Button>
                    </div>
                  </div>
                )}

              {/* Price Summary */}
              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Ticket Price Total</span>
                  <span>€{getCartTotal().toFixed(2)}</span>
                </div>
                {parsedRedeemPoints >= 100 && (
                  <>
                    <div className="flex justify-between text-sm text-green-600">
                      <span>Discount ({parsedRedeemPoints} points)</span>
                      <span>-€{calculateDiscount()}</span>
                    </div>
                    {isDiscountCapped() && (
                      <p className="text-xs text-amber-600">
                        ⚠️ Discount capped at 50% of total price (max €
                        {(getCartTotal() * 0.5).toFixed(2)})
                      </p>
                    )}
                  </>
                )}
                <div className="flex justify-between font-bold text-lg border-t pt-2">
                  <span>Final Price</span>
                  <span className="text-primary">€{calculateFinalPrice()}</span>
                </div>
              </div>

              {/* Points to Earn */}
              <div className="bg-primary/10 p-3 rounded-lg text-sm">
                <div className="flex items-center gap-2">
                  <Coins className="w-4 h-4 text-primary" />
                  <span>You'll earn reward points for this purchase!</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setIsPurchaseConfirmOpen(false);
                setCart({});
              }}
              disabled={isPurchasing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmPurchase}
              disabled={
                isPurchasing ||
                (parsedRedeemPoints > 0 && parsedRedeemPoints < 100) ||
                redeemExceedsBalance
              }
            >
              {isPurchasing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Processing...
                </>
              ) : (
                `Pay €${calculateFinalPrice()}`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {event && (
        <TicketPurchaseModal
          isOpen={showSuccessModal}
          onClose={() => {
            setShowSuccessModal(false);
            setCart({});
            setPurchasedTicketId(null);
          }}
          event={event}
          ticketId={purchasedTicketId}
          quantity={
            Object.values(cart).reduce((s, i) => s + i.quantity, 0) || 1
          }
          cartItems={Object.values(cart)}
        />
      )}

      {/* Image Gallery Carousel */}
      <Dialog open={isGalleryOpen} onOpenChange={setIsGalleryOpen}>
        <DialogContent className="max-w-4xl w-full p-0 bg-black/95 border-none text-white overflow-hidden h-[80vh] flex flex-col">
          <div className="flex-1 relative flex items-center justify-center w-full h-full">
            {images && images.length > 0 && (
              <>
                <div className="relative w-full h-full flex items-center justify-center p-4">
                  <img
                    src={images[currentImageIndex]}
                    alt={`Event photo ${currentImageIndex + 1}`}
                    className="max-w-full max-h-full object-contain"
                  />
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 rounded-full h-12 w-12"
                  onClick={(e) => {
                    e.stopPropagation();
                    prevImage();
                  }}
                >
                  <ChevronLeft className="w-8 h-8" />
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 rounded-full h-12 w-12"
                  onClick={(e) => {
                    e.stopPropagation();
                    nextImage();
                  }}
                >
                  <ChevronRight className="w-8 h-8" />
                </Button>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/50 px-4 py-2 rounded-full text-sm font-medium">
                  {currentImageIndex + 1} / {images.length}
                </div>
              </>
            )}
          </div>

          {/* Thumbnail strip */}
          <div className="h-20 bg-black/80 flex items-center justify-center gap-2 p-2 overflow-x-auto">
            {images &&
              images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentImageIndex(idx)}
                  className={`relative h-16 w-24 rounded-md overflow-hidden flex-shrink-0 transition-all ${
                    currentImageIndex === idx
                      ? "ring-2 ring-primary opacity-100"
                      : "opacity-50 hover:opacity-80"
                  }`}
                >
                  <img
                    src={img}
                    alt={`Thumbnail ${idx + 1}`}
                    className="w-full h-full object-cover"
                  />
                </button>
              ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EventDetail;
