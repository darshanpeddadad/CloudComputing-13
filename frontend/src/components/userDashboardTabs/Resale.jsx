import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router';
import { Calendar, Ticket, XCircle, AlertCircle } from "lucide-react";
import { baseUrl } from "@/routes";
import { toast } from "sonner";

const Resale = () => {
    const { user } = useSelector((state) => state.auth);
    const [tickets, setTickets] = useState([]);
    const [listings, setListings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        if (!user?.user?.id) return;

        const fetchData = async () => {
            setLoading(true);
            const config = {
                headers: {
                    Authorization: `Bearer ${user.access_token || user.user.access_token}`,
                },
            };

            try {
                // 1. Fetch User Tickets
                const ticketsRes = await axios.get(`${baseUrl}users/${user.user.id}/tickets`, {
                    ...config,
                    params: {
                        page: page,
                        page_size: pageSize,
                    }
                });

                const ticketsData = ticketsRes.data?.data || ticketsRes.data;
                const allTickets = ticketsData?.items || (Array.isArray(ticketsData) ? ticketsData : []);

                // Filter for 'listed' status
                // Note: The backend status for listed tickets is 'listed'
                const listedTickets = allTickets.filter(item => item.status?.toLowerCase() === 'listed');

                if (ticketsData?.pagination?.pages) {
                    setTotalPages(ticketsData.pagination.pages);
                } else {
                    setTotalPages(1);
                }

                // 2. Fetch Active Listings to get listing_id
                // We need this because the ticket object doesn't have the listing_id directly
                const listingsRes = await axios.get(`${baseUrl}resale/listings`, config);
                const activeListings = listingsRes.data || [];
                setListings(activeListings);

                // 3. Map tickets to listings
                const ticketsWithListings = listedTickets.map(ticket => {
                    const listing = activeListings.find(l => l.ticket_id === ticket.ticket_id);
                    return {
                        ...ticket,
                        listing_id: listing?.id
                    };
                });

                setTickets(ticketsWithListings);

            } catch (err) {
                console.error("Error fetching data:", err);
                toast.error("Failed to load resale tickets");
            } finally {
                setLoading(false);
            }
        };

        fetchData();

    }, [user, page, pageSize]);

    const handleCancelResale = async (listingId) => {
        if (!listingId) {
            toast.error("Listing ID not found");
            return;
        }

        try {
            const config = {
                headers: {
                    Authorization: `Bearer ${user.access_token || user.user.access_token}`,
                },
            };

            await axios.post(`${baseUrl}resale/listings/${listingId}/cancel`, {}, config);

            toast.success("Resale cancelled successfully");

            // Remove the cancelled ticket from the list
            setTickets(prev => prev.filter(t => t.listing_id !== listingId));

        } catch (err) {
            console.error("Error cancelling resale:", err);
            toast.error(err.response?.data?.detail || "Failed to cancel resale");
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'issued':
                return 'text-green-600 border-green-600/20 bg-green-50';
            case 'listed':
                return 'text-yellow-600 border-yellow-600/20 bg-yellow-50';
            case 'sold':
                return 'text-blue-600 border-blue-600/20 bg-blue-50';
            case 'cancelled':
                return 'text-red-600 border-red-600/20 bg-red-50';
            case 'expired':
                return 'text-gray-600 border-gray-600/20 bg-gray-50';
            default:
                return 'text-gray-600 border-gray-600/20 bg-gray-50';
        }
    };

    return (
        <div className="space-y-6">
            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : tickets.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    <Ticket className="w-12 h-12 mb-4 text-primary/20" />
                    <p>No tickets listed for resale.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {tickets.map((ticket) => (
                        <Card key={ticket.ticket_id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] bg-white/60 dark:bg-card/60 backdrop-blur-sm">
                            <div className="flex flex-col md:flex-row h-full md:h-40">
                                {/* Image Section */}
                                <div className="w-full md:w-64 h-40 md:h-full shrink-0 relative overflow-hidden bg-muted">
                                    <Link to={`/events/${ticket.event_id}`} className="block w-full h-full">
                                        {ticket.event_image ? (
                                            <img
                                                src={ticket.event_image}
                                                alt={ticket.event_name}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center bg-primary/5 text-primary/20">
                                                <Ticket className="w-12 h-12" />
                                            </div>
                                        )}
                                        <div className="absolute inset-0 bg-linear-to-t from-black/60 to-transparent md:bg-linear-to-r" />
                                    </Link>
                                </div>

                                {/* Content Section */}
                                <div className="flex-1 p-4 md:p-6 flex flex-col justify-between">
                                    <div className="flex justify-between items-start gap-4">
                                        <div className="space-y-1">
                                            <Link to={`/events/${ticket.event_id}`}>
                                                <h3 className="text-xl font-bold line-clamp-1 group-hover:text-primary transition-colors">
                                                    {ticket.event_name || "Unknown Event"}
                                                </h3>
                                            </Link>
                                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                <div className="flex items-center gap-1.5">
                                                    <Calendar className="w-4 h-4 text-primary/70" />
                                                    <span>{ticket.event_date ? new Date(ticket.event_date).toLocaleDateString() : "Date N/A"}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <Badge variant="secondary" className="bg-primary/5 text-primary border-primary/10">
                                                        Ticket #{ticket.ticket_id}
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-lg font-bold text-primary">
                                            {ticket.price !== undefined ? `${ticket.price}€` : "Free"}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-primary/5">
                                        <div className="flex items-center gap-2">
                                            <Badge
                                                variant="outline"
                                                className={`${getStatusColor(ticket.status)} capitalize`}
                                            >
                                                {ticket.status || "Active"}
                                            </Badge>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="border-red-500/20 text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors"
                                                onClick={() => handleCancelResale(ticket.listing_id)}
                                                disabled={!ticket.listing_id}
                                            >
                                                <XCircle className="w-3.5 h-3.5 mr-2" />
                                                Cancel Resale
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="flex justify-center items-center gap-2 mt-6">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1 || loading}
                        className="border-primary/20 hover:bg-primary/5"
                    >
                        Previous
                    </Button>
                    <div className="flex items-center gap-1 px-2">
                        <span className="text-sm font-medium text-muted-foreground">Page</span>
                        <span className="text-sm font-bold text-primary">{page}</span>
                        <span className="text-sm font-medium text-muted-foreground">of {totalPages}</span>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => p + 1)}
                        disabled={page >= totalPages || loading}
                        className="border-primary/20 hover:bg-primary/5"
                    >
                        Next
                    </Button>
                </div>
            )}
        </div>
    )
}

export default Resale