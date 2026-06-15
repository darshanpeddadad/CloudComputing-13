import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router';
import { Search, Calendar, Ticket, RefreshCw, AlertCircle } from "lucide-react";
import { baseUrl } from "@/routes";
import { toast } from "sonner";
import ResellTicketModal from "./ResellTicketModal";

const Mytickets = () => {
    const { user } = useSelector((state) => state.auth);
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(100); // Increased to 100 so grouping applies to all tickets
    const [totalPages, setTotalPages] = useState(1);
    const [search, setSearch] = useState("");

    // Resell Modal State
    const [isResellModalOpen, setIsResellModalOpen] = useState(false);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [resellLoading, setResellLoading] = useState(false);

    const fetchTickets = () => {
        if (!user?.user?.id) return;

        setLoading(true);
        const config = {
            headers: {
                Authorization: `Bearer ${user.access_token || user.user.access_token}`,
            },
            params: {
                page: page,
                page_size: pageSize,
            },
        };

        axios
            .get(`${baseUrl}users/${user.user.id}/tickets`, config)
            .then((res) => {
                const data = res.data?.data || res.data;
                const items = data?.items || (Array.isArray(data) ? data : []);
                // Filter out listed tickets before grouping
                const filteredItems = items.filter((item) => item.status !== "listed");
                // Group tickets strictly by event_id, price, and status to prevent visual clutter
                const groupedItems = Object.values(filteredItems.reduce((acc, ticket) => {
                    const status = ticket.status?.toLowerCase() || 'active';
                    const isEventOver = ticket.event_date && new Date() > new Date(new Date(ticket.event_date).getTime() + 24 * 60 * 60 * 1000);
                    // Tickets that are "issued" and NOT expired can be grouped. Others kept separate if needed.
                    // Actually, grouping all statuses by event makes it cleaner.
                    const key = `${ticket.event_id}-${ticket.ticket_type_id || ticket.price || 0}-${status}-${isEventOver}`;
                    
                    if (!acc[key]) {
                        acc[key] = { ...ticket, quantity: 1, grouped_ticket_ids: [ticket.ticket_id] };
                    } else {
                        acc[key].quantity += 1;
                        acc[key].grouped_ticket_ids.push(ticket.ticket_id);
                    }
                    return acc;
                }, {}));

                setTickets(groupedItems);
                console.log(items);

                if (data?.pagination?.pages) {
                    setTotalPages(data.pagination.pages);
                } else {
                    setTotalPages(1);
                }
            })
            .catch((err) => {
                console.error("Error fetching tickets:", err);
            })
            .finally(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchTickets();
    }, [user, page, pageSize]);

    const getTicketStatusInfo = (ticket) => {
        const status = ticket.status?.toLowerCase();
        const eventDate = ticket.event_date ? new Date(ticket.event_date) : null;
        const isEventOver = eventDate && new Date() > new Date(eventDate.getTime() + 24 * 60 * 60 * 1000);

        if (status === 'cancelled') return { label: 'Cancelled', className: 'text-red-600 border-red-600/20 bg-red-50' };
        if (status === 'refunded') return { label: 'Refunded', className: 'text-gray-600 border-gray-600/20 bg-gray-50' };

        if (isEventOver) return { label: 'Completed', className: 'text-gray-600 border-gray-600/20 bg-gray-50' };

        switch (status) {
            case 'issued':
                return { label: 'Issued', className: 'text-green-600 border-green-600/20 bg-green-50' };
            case 'listed':
                return { label: 'Listed for Resale', className: 'text-yellow-600 border-yellow-600/20 bg-yellow-50' };
            case 'checked_in':
                return { label: 'Checked In', className: 'text-blue-600 border-blue-600/20 bg-blue-50' };
            case 'transferred':
                return { label: 'Transferred', className: 'text-purple-600 border-purple-600/20 bg-purple-50' };
            default:
                return { label: status || 'Active', className: 'text-gray-600 border-gray-600/20 bg-gray-50' };
        }
    };

    const handleResellClick = (ticket) => {
        setSelectedTicket(ticket);
        setIsResellModalOpen(true);
    };

    const handleResellSubmit = async ({ askingPrice, notes, currency, quantityToSell = 1 }) => {
        if (!selectedTicket) return;

        setResellLoading(true);
        try {
            const ticketIdsToSell = selectedTicket.grouped_ticket_ids 
                ? selectedTicket.grouped_ticket_ids.slice(0, quantityToSell) 
                : [selectedTicket.ticket_id];

            const config = {
                headers: {
                    Authorization: `Bearer ${user.access_token || user.user.access_token}`,
                },
            };

            await Promise.all(ticketIdsToSell.map(t_id => {
                const payload = {
                    allow_offers: true,
                    asking_price: askingPrice,
                    currency: currency || selectedTicket.currency || "EUR",
                    expires_at: "2025-12-31T23:59:59Z", // Future date
                    notes: notes,
                    ticket_id: t_id
                };
                return axios.post(`${baseUrl}resale/listings`, payload, config);
            }));

            toast.success(`Successfully listed ${quantityToSell} ticket(s) for resale!`);
            setIsResellModalOpen(false);
            setSelectedTicket(null);
            fetchTickets(); // Refresh list
        } catch (error) {
            console.error("Error listing ticket for resale:", error);
            toast.error(error.response?.data?.message || "Failed to list ticket for resale.");
        } finally {
            setResellLoading(false);
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
                    <p>No tickets found.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {tickets.map((ticket) => {
                        const statusInfo = getTicketStatusInfo(ticket);
                        return (
                            <Card key={ticket.ticket_id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] bg-white/60 dark:bg-card/60 backdrop-blur-sm">
                                <div className="flex flex-col md:flex-row h-full md:h-40">
                                    {/* Image Section */}
                                    <div className="w-full md:w-64 h-40 md:h-full shrink-0 relative overflow-hidden bg-muted">
                                        <Link to={`/events/${ticket.event_id}`} className="block w-full h-full">
                                            {/* if theres no image use "https://gdsd2025.s3.eu-central-1.amazonaws.com/images/default.png" also if the image is not from the gdsd2025 bucket use default image */}
                                            <img
                                                src={ticket.event_image}
                                                alt={ticket.event_name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
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
                                                            {ticket.ticket_type ? ticket.ticket_type : ''}{ticket.quantity > 1 ? ` · Qty: ${ticket.quantity}` : ''}
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
                                                    className={`${statusInfo.className} capitalize`}
                                                >
                                                    {statusInfo.label}
                                                </Badge>
                                            </div>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="border-primary/20 hover:bg-primary/5 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                    disabled={true} // disabled for now, coming soon
                                                >
                                                    <RefreshCw className="w-3.5 h-3.5 mr-2" />
                                                    Refund
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="border-primary/20 hover:bg-primary/5 hover:text-primary transition-colors"
                                                    disabled={!ticket.resale_allowed || ['Cancelled', 'Completed', 'Refunded'].includes(statusInfo.label)}
                                                    onClick={() => handleResellClick(ticket)}
                                                >
                                                    <Ticket className="w-3.5 h-3.5 mr-2" />
                                                    Resell
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
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

            <ResellTicketModal
                isOpen={isResellModalOpen}
                onClose={() => setIsResellModalOpen(false)}
                onConfirm={handleResellSubmit}
                ticket={selectedTicket}
                loading={resellLoading}
            />
        </div>
    )
}

export default Mytickets