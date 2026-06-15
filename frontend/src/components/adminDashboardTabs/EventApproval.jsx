import React from 'react'
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Search, Calendar, Check, X } from "lucide-react";
import { Link } from 'react-router';
import { baseUrl } from '@/routes';

import { toast } from "sonner";

const EventApproval = () => {
    const { user } = useSelector((state) => state.auth);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [totalPages, setTotalPages] = useState(1);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
            setPage(1); // Reset to first page on new search
        }, 500);
        return () => clearTimeout(timer);
    }, [search]);

    useEffect(() => {
        if (!user?.access_token) return;

        setLoading(true);
        const config = {
            headers: {
                Authorization: `Bearer ${user.access_token}`,
            },
            params: {
                page: page,
                page_size: pageSize,
                search: debouncedSearch || null,
            },
        };

        axios
            .get(`${baseUrl}events/pending`, config)
            .then((res) => {
                const data = res.data?.data;
                const items = data?.items || [];
                setEvents(items);
                console.log(items);

                if (data?.pagination?.pages) {
                    setTotalPages(data.pagination.pages);
                } else {
                    setTotalPages(1);
                }
            })
            .catch((err) => {
                console.error("Error fetching events:", err);
            })
            .finally(() => {
                setLoading(false);
            });
    }, [user, page, pageSize, debouncedSearch]);

    const handleApprove = async (eventId) => {
        if (!user?.access_token) return;
        try {
            await axios.post(
                `${baseUrl}events/${eventId}/approve`,
                {},
                {
                    headers: { Authorization: `Bearer ${user.access_token}` },
                }
            );
            toast.success("Event approved successfully");
            setEvents((prev) => prev.filter((e) => e.id !== eventId));
        } catch (error) {
            console.error("Error approving event:", error);
            toast.error("Failed to approve event");
        }
    };

    const handleReject = async (eventId) => {
        if (!user?.access_token) return;
        try {
            await axios.post(
                `${baseUrl}events/${eventId}/reject`,
                {},
                {
                    headers: { Authorization: `Bearer ${user.access_token}` },
                }
            );
            toast.success("Event rejected successfully");
            setEvents((prev) => prev.filter((e) => e.id !== eventId));
        } catch (error) {
            console.error("Error rejecting event:", error);
            toast.error("Failed to reject event");
        }
    };

    return (
        <div className="space-y-6">
            {/* Search Bar */}
            <div className="flex justify-end">
                <div className="relative w-full md:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search events..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-white/50 dark:bg-card/50 border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30 transition-all placeholder:text-muted-foreground/70"
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : events.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    No pending events found
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {events.map((event) => (
                        <Card key={event.id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] bg-white/60 dark:bg-card/60 backdrop-blur-sm">
                            <div className="flex flex-col md:flex-row h-full md:h-40">
                                {/* Image Section */}
                                <div className="w-full md:w-64 h-40 md:h-full shrink-0 relative overflow-hidden">
                                    <Link to={`/events/${event.id}`} className="block w-full h-full">
                                        <img
                                            src={event?.images && event.images[0]}
                                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                        />
                                        <div className="absolute inset-0 bg-linear-to-t from-black/60 to-transparent md:bg-linear-to-r" />
                                    </Link>
                                </div>

                                {/* Content Section */}
                                <div className="flex-1 p-4 md:p-6 flex flex-col justify-between">
                                    <div className="flex justify-between items-start gap-4">
                                        <div className="space-y-1">
                                            <Link to={`/events/${event.id}`}>
                                                <h3 className="text-xl font-bold line-clamp-1 group-hover:text-primary transition-colors">
                                                    {event.name || event.title}
                                                </h3>
                                            </Link>
                                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                <div className="flex items-center gap-1.5">
                                                    <Calendar className="w-4 h-4 text-primary/70" />
                                                    <span>{event.date || event.start_date ? new Date(event.date || event.start_date).toLocaleDateString() : "N/A"}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 hover:bg-yellow-500/20">
                                                        Pending Approval
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-lg font-bold text-primary">
                                            {event.price !== undefined ? (event.price === 0 ? 'Free' : `${event.price}€`) : 'Free'}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-end gap-3 mt-4 pt-4 border-t border-primary/5">
                                        <Button
                                            variant="outline"
                                            className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50 transition-all duration-300"
                                            onClick={() => handleReject(event.id)}
                                        >
                                            <X className="w-4 h-4 mr-2" />
                                            Reject
                                        </Button>
                                        <Button
                                            className="bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg transition-all duration-300"
                                            onClick={() => handleApprove(event.id)}
                                        >
                                            <Check className="w-4 h-4 mr-2" />
                                            Approve
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="flex justify-center items-center gap-2 mt-8">
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
                        disabled={events.length < pageSize || loading}
                        className="border-primary/20 hover:bg-primary/5"
                    >
                        Next
                    </Button>
                </div>
            )}
        </div>
    )
}

export default EventApproval