import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router';
import { baseUrl } from "@/routes";
import { Calendar, Users, Edit, Ticket } from "lucide-react";

const Myevents = () => {
    const { user } = useSelector((state) => state.auth);
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        if (!user?.user?.id) return;

        setLoading(true);
        const config = {
            headers: {
                Authorization: `Bearer ${user.access_token}`,
            },
            params: {
                page: page,
                page_size: pageSize,
            },
        };

        axios
            .get(`${baseUrl}users/${user.user.id}/events`, config)
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

    }, [user, page, pageSize]);

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'published':
            case 'approved':
                return "text-green-600 border-green-200 bg-green-50";
            case 'pending':
                return "text-yellow-600 border-yellow-200 bg-yellow-50";
            case 'draft':
                return "text-gray-600 border-gray-200 bg-gray-50";
            case 'cancelled':
            case 'rejected':
                return "text-red-600 border-red-200 bg-red-50";
            case 'completed':
                return "text-blue-600 border-blue-200 bg-blue-50";
            default:
                return "text-gray-600 border-gray-200 bg-gray-50";
        }
    };

    return (
        <div className="space-y-6">

            {/* Search bar -Next week */}
            {/* <div className="flex justify-end mb-4">
                <input
                    type="text"
                    placeholder="Search events..."
                    className="border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div> */}

            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : events.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    <Calendar className="w-12 h-12 mb-4 text-primary/20" />
                    <p>No events found.</p>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 gap-4">
                        {events.map((event) => (

                            <Card key={event.id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg hover:scale-[1.01] bg-white/60 dark:bg-card/60 backdrop-blur-sm">
                                <div className="flex flex-col md:flex-row h-full md:h-40">
                                    {/* Image Section */}
                                    <div className="w-full md:w-64 h-40 md:h-full shrink-0 relative overflow-hidden bg-muted">
                                        <Link to={`/events/${event.id}`} className="block w-full h-full">
                                            <img
                                                src={event.images && event.images.length > 0 ? event.images[0] : "https://gdsd2025.s3.eu-central-1.amazonaws.com/images/default-1.jpg"}
                                                alt={event.title}
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
                                                        {event.title}
                                                    </h3>
                                                </Link>
                                                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                    <div className="flex items-center gap-1.5">
                                                        <Calendar className="w-4 h-4 text-primary/70" />
                                                        <span>{event.start_date ? new Date(event.start_date).toLocaleDateString() : "N/A"}</span>
                                                    </div>
                                                    <div className="flex items-center gap-1.5">
                                                        <Users className="w-4 h-4 text-primary/70" />
                                                        <span>Max: {event.max_attendees}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-lg font-bold text-primary">
                                                {event.price !== undefined ? `${event.price}€` : "Free"}
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-primary/5">
                                            <div className="flex items-center gap-2">
                                                {event.status && (
                                                    <Badge
                                                        variant="outline"
                                                        className={`${getStatusColor(event.status)} capitalize `}
                                                    >
                                                        {event.status}
                                                    </Badge>
                                                )}
                                            </div>
                                            <div className="flex gap-2">
                                                <Link to={`/events/edit/${event.id}`}>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        className="border-primary/20 hover:bg-primary/5 hover:text-primary transition-colors"
                                                    >
                                                        <Edit className="w-3.5 h-3.5 mr-2" />
                                                        Edit Event
                                                    </Button>
                                                </Link>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>

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
                </>
            )}
        </div>
    );
};

export default Myevents;
