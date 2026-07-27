import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from 'react-router';
import { Calendar, Users, BookmarkMinus } from "lucide-react";
import userApiService from "@/services/userApiService";
import { toast } from "sonner";

const Bookmarks = () => {
    const { user } = useSelector((state) => state.auth);
    const [bookmarks, setBookmarks] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchBookmarks = async () => {
        if (!user?.user?.id) return;

        setLoading(true);
        try {
            const data = await userApiService.getBookmarks(user.user.id);
            setBookmarks(data);
        } catch (err) {
            console.error("Error fetching bookmarks:", err);
            toast.error("Failed to fetch bookmarks");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBookmarks();
    }, [user]);

    const handleRemoveBookmark = async (eventId) => {
        try {
            await userApiService.removeBookmark(user.user.id, eventId);
            toast.success("Bookmark removed");
            // Optimistically remove from state
            setBookmarks((prev) => prev.filter((b) => b.event_id !== eventId));
        } catch (err) {
            console.error("Error removing bookmark:", err);
            toast.error("Failed to remove bookmark");
        }
    };



    return (
        <div className="space-y-6">
            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : bookmarks.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    <BookmarkMinus className="w-12 h-12 mb-4 text-primary/20" />
                    <p>No bookmarked events found.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {bookmarks.map((bookmark) => {
                        const event = bookmark.event;
                        return (
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
                                                {(() => {
                                                    const now = new Date();
                                                    const eventEnd = new Date(`${event.end_date}T${event.end_time}`);
                                                    const isEnded = now > eventEnd;

                                                    return (
                                                        <Badge
                                                            variant="outline"
                                                            className={`${isEnded
                                                                ? "text-gray-600 border-gray-200 bg-gray-50"
                                                                : "text-green-600 border-green-200 bg-green-50"
                                                                } capitalize`}
                                                        >
                                                            {isEnded ? "Ended" : "Upcoming"}
                                                        </Badge>
                                                    );
                                                })()}
                                            </div>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleRemoveBookmark(event.id)}
                                                    className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 transition-colors"
                                                >
                                                    <BookmarkMinus className="w-3.5 h-3.5 mr-2" />
                                                    Remove Bookmark
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
        </div>
    );
};

export default Bookmarks;