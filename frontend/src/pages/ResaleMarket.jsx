import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from 'react-router';
import { Calendar, Ticket, ShoppingCart, Loader2 } from "lucide-react";
import { baseUrl } from "@/routes";
import { toast } from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import TicketPurchaseModal from "@/components/events/TicketPurchaseModal";

const ResaleMarket = () => {
    const { user, isAuthenticated } = useSelector((state) => state.auth || {});
    const navigate = useNavigate();
    const [listings, setListings] = useState([]);
    const [loading, setLoading] = useState(true);

    const [selectedListing, setSelectedListing] = useState(null);
    const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false);
    const [isPurchasing, setIsPurchasing] = useState(false);

    const [showSuccessModal, setShowSuccessModal] = useState(false);
    const [purchasedTicketId, setPurchasedTicketId] = useState(null);
    const [purchasedEvent, setPurchasedEvent] = useState(null);

    useEffect(() => {
        const fetchListings = async () => {
            setLoading(true);
            try {
                const config = {};
                if (isAuthenticated && user?.access_token) {
                    config.headers = {
                        Authorization: `Bearer ${user.access_token}`,
                    };
                }

                const res = await axios.get(`${baseUrl}resale/listings`, config);
                setListings(res.data || []);
            } catch (err) {
                console.error("Error fetching listings:", err);
                if (err.response?.status === 401) {
                    toast.error("Unauthorized to view listings. Please login.");
                } else {
                    toast.error("Failed to load resale market listings");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchListings();
    }, [isAuthenticated, user]);

    const handleBuyClick = (listing) => {
        if (!isAuthenticated) {
            toast.error("Please login to purchase tickets", {
                action: {
                    label: "Login",
                    onClick: () => navigate("/login")
                }
            });
            return;
        }
        setSelectedListing(listing);
        setIsPurchaseModalOpen(true);
    };

    const handleConfirmPurchase = async () => {
        if (!selectedListing) return;

        setIsPurchasing(true);
        try {
            const config = {
                headers: {
                    Authorization: `Bearer ${user.access_token || user.user.access_token}`,
                },
            };

            const res = await axios.post(`${baseUrl}resale/listings/${selectedListing.id}/purchase`, {}, config);

            toast.success("Ticket purchased successfully!");
            setIsPurchaseModalOpen(false);

            const newTicketId = res.data?.ticket_id || res.data?.data?.ticket_id;
            if (newTicketId) {
                setPurchasedTicketId(newTicketId);
                setPurchasedEvent(selectedListing.event);
                setShowSuccessModal(true);
            }

            setListings(prev => prev.filter(l => l.id !== selectedListing.id));

        } catch (err) {
            console.error("Error purchasing ticket:", err);
            toast.error(err.response?.data?.detail || "Failed to purchase ticket");
        } finally {
            setIsPurchasing(false);
        }
    };

    return (
        <div className="min-h-screen bg-background pt-24 pb-12">
            <div className="fixed inset-0 bg-linear-to-br from-blue-50 via-white to-sky-50 dark:from-blue-950/30 dark:via-background dark:to-sky-950/30 -z-10" />
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(59,130,246,0.15),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(14,165,233,0.12),transparent_50%)] -z-10" />

            <div className="container mx-auto px-4">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl md:text-4xl font-bold bg-linear-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                            Resale Market
                        </h1>
                        <p className="text-muted-foreground mt-2">
                            Buy tickets from other users safely and securely
                        </p>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : listings.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                        <Ticket className="w-12 h-12 mb-4 text-primary/20" />
                        <p>No tickets currently available for resale.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {listings.map((listing) => (
                            <Card key={listing.id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] bg-white/60 dark:bg-card/60 backdrop-blur-sm flex flex-col">
                                <div className="h-48 overflow-hidden bg-muted relative">
                                    {listing.event?.images && listing.event.images.length > 0 ? (
                                        <img
                                            src={listing.event.images[0]}
                                            alt={listing.event.title}
                                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/20">
                                            <Ticket className="w-12 h-12" />
                                        </div>
                                    )}
                                    <div className="absolute top-2 right-2">
                                        <Badge className="bg-white/90 text-primary hover:bg-white shadow-sm backdrop-blur-sm">
                                            {listing.currency || "EUR"} {listing.asking_price || listing.price}
                                        </Badge>
                                    </div>
                                </div>

                                <div className="p-5 flex-1 flex flex-col">
                                    <div className="flex-1 space-y-3">
                                        <div className="space-y-1">
                                            <h3 className="text-xl font-bold line-clamp-1 group-hover:text-primary transition-colors">
                                                {listing.event?.title || "Unknown Event"}
                                            </h3>
                                            <p className="text-sm text-muted-foreground line-clamp-1">
                                                {listing.event?.location || "Location N/A"}
                                            </p>
                                        </div>

                                        {listing.notes && (
                                            <p className="text-sm text-muted-foreground line-clamp-2 italic">
                                                "{listing.notes}"
                                            </p>
                                        )}

                                        <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-4 h-4" />
                                                <span>
                                                    {listing.event?.start_date ? new Date(listing.event.start_date).toLocaleDateString() : "Date N/A"}
                                                    {listing.event?.start_time ? ` • ${listing.event.start_time.slice(0, 5)}` : ""}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2 text-xs opacity-80">
                                                <span>Ticket #{listing.ticket_id?.slice(0, 8)}...</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-6 pt-4 border-t border-primary/5 flex items-center justify-between">
                                        <div className="text-xs text-muted-foreground">
                                            {listing.allow_offers ? "Offers allowed" : "Fixed Price"}
                                        </div>
                                        <Button
                                            size="sm"
                                            className="shadow-lg shadow-primary/20 hover:shadow-primary/30"
                                            onClick={() => handleBuyClick(listing)}
                                        >
                                            <ShoppingCart className="w-4 h-4 mr-2" />
                                            Buy Now
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                )}
            </div>

            <Dialog open={isPurchaseModalOpen} onOpenChange={setIsPurchaseModalOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Confirm Purchase</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to purchase this ticket?
                        </DialogDescription>
                    </DialogHeader>

                    {selectedListing && (
                        <div className="py-4 space-y-4">
                            <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                                <span className="text-sm font-medium">Event</span>
                                <span className="text-sm font-bold text-right">{selectedListing.event?.title}</span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                                <span className="text-sm font-medium">Date & Time</span>
                                <span className="text-sm text-right">
                                    {selectedListing.event?.start_date} • {selectedListing.event?.start_time?.slice(0, 5)}
                                </span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                                <span className="text-sm font-medium">Location</span>
                                <span className="text-sm text-right">{selectedListing.event?.location}</span>
                            </div>
                            <div className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                                <span className="text-sm font-medium">Price</span>
                                <span className="text-lg font-bold text-primary">
                                    {selectedListing.currency || "EUR"} {selectedListing.asking_price || selectedListing.price}
                                </span>
                            </div>
                            {selectedListing.notes && (
                                <div className="p-3 bg-muted/50 rounded-lg space-y-1">
                                    <span className="text-sm font-medium block">Seller Notes</span>
                                    <p className="text-sm text-muted-foreground italic">"{selectedListing.notes}"</p>
                                </div>
                            )}
                        </div>
                    )}

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setIsPurchaseModalOpen(false)} disabled={isPurchasing}>
                            Cancel
                        </Button>
                        <Button onClick={handleConfirmPurchase} disabled={isPurchasing}>
                            {isPurchasing ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                "Confirm Purchase"
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {showSuccessModal && purchasedEvent && (
                <TicketPurchaseModal
                    isOpen={showSuccessModal}
                    onClose={() => setShowSuccessModal(false)}
                    event={purchasedEvent}
                    ticketId={purchasedTicketId}
                />
            )
            }
        </div >
    );
};

export default ResaleMarket;
