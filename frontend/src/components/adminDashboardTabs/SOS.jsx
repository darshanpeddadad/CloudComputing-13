import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import axios from 'axios';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, Clock, User, CheckCircle, AlertTriangle, XCircle, ShieldAlert } from "lucide-react";
import { baseUrl } from '@/routes';
import { toast } from "sonner";
import sosApiService from '@/services/sosApiService';

const SOS = () => {
    const { user } = useSelector((state) => state.auth);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        fetchAlerts();
    }, [user, page, pageSize]);

    const fetchAlerts = () => {
        if (!user?.access_token) return;

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
            .get(`${baseUrl}sos/`, config)
            .then((res) => {
                const data = res.data;
                // API response structure: { items: [], pagination: { ... } }
                setAlerts(data.items || []);
                if (data.pagination) {
                    setTotalPages(data.pagination.total_pages || 1);
                }
            })
            .catch((err) => {
                console.error("Error fetching SOS alerts:", err);
                toast.error("Failed to fetch SOS alerts");
            })
            .finally(() => {
                setLoading(false);
            });
    };

    const handleStatusUpdate = async (alertId, status) => {
        if (!user?.access_token) return;
        try {
            await sosApiService.updateAlertStatus(alertId, status);
            toast.success(`Alert marked as ${status}`);
            fetchAlerts(); // Refresh list
        } catch (error) {
            console.error(`Error marking alert as ${status}:`, error);
            toast.error(`Failed to mark alert as ${status}`);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return "N/A";
        return new Date(dateString).toLocaleString();
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-primary">SOS Alerts</h2>
            </div>

            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : alerts.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    No SOS alerts found
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {alerts.map((alert) => (
                        <Card key={alert.id} className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg bg-white/60 dark:bg-card/60 backdrop-blur-sm">
                            <CardContent className="p-6">
                                <div className="flex flex-col md:flex-row gap-6">
                                    {/* Icon/Status Section */}
                                    <div className="flex md:flex-col items-center justify-center gap-2 min-w-[100px]">
                                        <div className={`p-4 rounded-full ${alert.status === 'active' ? 'bg-red-100 text-red-600' :
                                            alert.status === 'resolved' ? 'bg-green-100 text-green-600' :
                                                'bg-gray-100 text-orange-600'
                                            }`}>
                                            <AlertTriangle className="w-8 h-8" />
                                        </div>
                                        {/* checks the status fake, active, resolved and badge variant accordingly */}
                                        <Badge variant={alert.status === 'active' ? 'destructive' : alert.status === 'fake' ? 'destructive' : 'secondary'} className="uppercase">
                                            {alert.status}
                                        </Badge>
                                    </div>

                                    {/* Content Section */}
                                    <div className="flex-1 space-y-4">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="text-lg font-bold text-foreground">
                                                    Alert ID: {alert.id.substring(0, 8)}...
                                                </h3>
                                                <p className="text-muted-foreground mt-1">
                                                    {alert.message || "No message provided"}
                                                </p>
                                            </div>
                                            <div className="text-right text-sm text-muted-foreground">
                                                <div className="flex items-center gap-1 justify-end">
                                                    <Clock className="w-4 h-4" />
                                                    {formatDate(alert.created_at)}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <User className="w-4 h-4 text-primary" />
                                                <span>User: {alert.user.first_names} {alert.user.last_name}</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-muted-foreground">
                                                <MapPin className="w-4 h-4 text-primary" />
                                                <span>Location: {alert.latitude.toFixed(6)}, {alert.longitude.toFixed(6)}</span>
                                            </div>
                                            {alert.event_id && (
                                                <div className="flex items-center gap-2 text-muted-foreground">
                                                    <ShieldAlert className="w-4 h-4 text-primary" />
                                                    <span>Event: {alert.event.title}</span>
                                                </div>
                                            )}
                                        </div>

                                        {/* Actions */}
                                        {alert.status === 'active' && (
                                            <div className="flex items-center gap-3 pt-4 border-t border-primary/5">
                                                <Button
                                                    variant="outline"
                                                    className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                                    onClick={() => handleStatusUpdate(alert.id, 'fake')}
                                                >
                                                    <XCircle className="w-4 h-4 mr-2" />
                                                    Mark as Fake
                                                </Button>
                                                <Button
                                                    className="bg-green-600 hover:bg-green-700 text-white"
                                                    onClick={() => handleStatusUpdate(alert.id, 'resolved')}
                                                >
                                                    <CheckCircle className="w-4 h-4 mr-2" />
                                                    Resolve
                                                </Button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
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
                        disabled={page >= totalPages || loading}
                        className="border-primary/20 hover:bg-primary/5"
                    >
                        Next
                    </Button>
                </div>
            )}
        </div>
    );
};

export default SOS;