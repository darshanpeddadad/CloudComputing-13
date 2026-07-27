import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, Check, Search, X } from "lucide-react";
import { Link } from "react-router";
import { toast } from "sonner";
import { baseUrl } from "@/routes";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const FIELD_LABELS = {
  title: "Title",
  description: "Description",
  location: "Location",
  latitude: "Latitude",
  longitude: "Longitude",
  category_id: "Category",
  start_date: "Start Date",
  end_date: "End Date",
  start_time: "Start Time",
  end_time: "End Time",
  max_attendees: "Max Attendees",
  sos_enabled: "SOS Enabled",
};

const EventModification = () => {
  const { user } = useSelector((state) => state.auth);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [totalPages, setTotalPages] = useState(1);
  const [descriptionDialog, setDescriptionDialog] = useState({
    open: false,
    title: "",
    from: "",
    to: "",
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
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
        page,
        page_size: pageSize,
        status: "pending",
        search: debouncedSearch || null,
      },
    };

    axios
      .get(`${baseUrl}events/edit-requests`, config)
      .then((res) => {
        const data = res.data?.data;
        setRequests(data?.items || []);
        if (data?.pagination?.pages) {
          setTotalPages(data.pagination.pages);
        } else {
          setTotalPages(1);
        }
      })
      .catch((err) => {
        console.error("Error fetching edit requests:", err);
      })
      .finally(() => setLoading(false));
  }, [user, page, pageSize, debouncedSearch]);

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "approved":
        return "text-green-600 border-green-200 bg-green-50";
      case "rejected":
        return "text-red-600 border-red-200 bg-red-50";
      case "pending":
      default:
        return "text-yellow-600 border-yellow-200 bg-yellow-50";
    }
  };

  const formatValue = (field, value) => {
    if (value === null || value === undefined || value === "") return "N/A";
    if (field === "sos_enabled") return value ? "Yes" : "No";
    if (field === "start_date" || field === "end_date") {
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
    }
    if (field === "latitude" || field === "longitude") {
      const num = Number(value);
      return Number.isNaN(num) ? String(value) : num.toFixed(4);
    }
    return String(value);
  };

  const openDescriptionDialog = (title, from, to) => {
    setDescriptionDialog({
      open: true,
      title: title || "Description change",
      from: from ?? "",
      to: to ?? "",
    });
  };

  const handleApprove = async (requestId) => {
    if (!user?.access_token) return;
    try {
      await axios.post(
        `${baseUrl}events/edit-requests/${requestId}/approve`,
        {},
        { headers: { Authorization: `Bearer ${user.access_token}` } }
      );
      toast.success("Edit request approved");
      setRequests((prev) => prev.filter((req) => req.id !== requestId));
    } catch (error) {
      console.error("Error approving edit request:", error);
      toast.error("Failed to approve edit request");
    }
  };

  const handleReject = async (requestId) => {
    if (!user?.access_token) return;
    try {
      await axios.post(
        `${baseUrl}events/edit-requests/${requestId}/reject`,
        {},
        { headers: { Authorization: `Bearer ${user.access_token}` } }
      );
      toast.success("Edit request rejected");
      setRequests((prev) => prev.filter((req) => req.id !== requestId));
    } catch (error) {
      console.error("Error rejecting edit request:", error);
      toast.error("Failed to reject edit request");
    }
  };

  return (
    <div className="space-y-6">
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
      ) : requests.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
          No edit requests found.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4">
            {requests.map((request) => (
              <Card
                key={request.id}
                className="group overflow-hidden border-primary/10 hover:border-primary/30 transition-all duration-300 hover:shadow-lg bg-white/60 dark:bg-card/60 backdrop-blur-sm"
              >
                <div className="flex flex-col md:flex-row h-full">
                  <div className="w-full md:w-64 h-40 md:h-full shrink-0 relative overflow-hidden bg-muted">
                    <Link to={`/events/${request.event?.id}`} className="block w-full h-full">
                      <img
                        src={
                          request.event?.images?.[0] ||
                          "https://gdsd2025.s3.eu-central-1.amazonaws.com/images/default-1.jpg"
                        }
                        alt={request.event?.title || "Event"}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-linear-to-t from-black/60 to-transparent md:bg-linear-to-r" />
                    </Link>
                  </div>

                  <div className="flex-1 p-4 md:p-6 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                      <div className="space-y-1">
                        <Link to={`/events/${request.event?.id}`}>
                          <h3 className="text-xl font-bold line-clamp-1 group-hover:text-primary transition-colors">
                            {request.event?.title || "Untitled Event"}
                          </h3>
                        </Link>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Calendar className="w-4 h-4 text-primary/70" />
                          <span>
                            Submitted{" "}
                            {request.created_at
                              ? new Date(request.created_at).toLocaleString()
                              : "N/A"}
                          </span>
                        </div>
                        {request.requested_by?.name && (
                          <div className="text-sm text-muted-foreground">
                            Organizer: {request.requested_by.name}
                          </div>
                        )}
                      </div>
                      <Badge
                        variant="outline"
                        className={`${getStatusBadge(request.status)} capitalize`}
                      >
                        {request.status || "pending"}
                      </Badge>
                    </div>

                    <div className="border border-primary/10 rounded-xl overflow-hidden">
                      <div className="grid grid-cols-1 md:grid-cols-3 bg-primary/5 text-sm font-medium">
                        <div className="px-4 py-2">Field</div>
                        <div className="px-4 py-2">From</div>
                        <div className="px-4 py-2">To</div>
                      </div>
                      {Object.entries(request.changes || {}).map(([field, diff]) => {
                        const fromValue = diff?.from;
                        const toValue = diff?.to;
                        const showDescriptionModal =
                          field === "description" && (fromValue || toValue);
                        return (
                          <div
                            key={field}
                            className="grid grid-cols-1 md:grid-cols-3 border-t border-primary/10 text-sm"
                          >
                            <div className="px-4 py-2 font-medium text-muted-foreground">
                              {FIELD_LABELS[field] || field}
                              {showDescriptionModal && (
                                <button
                                  type="button"
                                  className="ml-2 text-xs text-primary underline underline-offset-4"
                                  onClick={() =>
                                    openDescriptionDialog(
                                      request.event?.title,
                                      fromValue,
                                      toValue
                                    )
                                  }
                                >
                                  View full
                                </button>
                              )}
                            </div>
                            <div className="px-4 py-2 text-muted-foreground">
                              {field === "description" ? (
                                <p className="line-clamp-2">
                                  {String(fromValue ?? "N/A")}
                                </p>
                              ) : (
                                formatValue(field, fromValue)
                              )}
                            </div>
                            <div className="px-4 py-2">
                              {field === "description" ? (
                                <p className="line-clamp-2">
                                  {String(toValue ?? "N/A")}
                                </p>
                              ) : (
                                formatValue(field, toValue)
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="flex items-center justify-end gap-3 border-t border-primary/5 pt-4">
                      <Button
                        variant="outline"
                        className="border-destructive/20 text-destructive hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50 transition-all duration-300"
                        onClick={() => handleReject(request.id)}
                      >
                        <X className="w-4 h-4 mr-2" />
                        Reject
                      </Button>
                      <Button
                        className="bg-green-600 hover:bg-green-700 text-white shadow-md hover:shadow-lg transition-all duration-300"
                        onClick={() => handleApprove(request.id)}
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
      <Dialog
        open={descriptionDialog.open}
        onOpenChange={(open) =>
          setDescriptionDialog((prev) => ({ ...prev, open }))
        }
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{descriptionDialog.title || "Description change"}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">From</div>
              <div className="rounded-md border border-border/60 bg-muted/30 p-3 whitespace-pre-wrap">
                {descriptionDialog.from || "N/A"}
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">To</div>
              <div className="rounded-md border border-border/60 bg-muted/30 p-3 whitespace-pre-wrap">
                {descriptionDialog.to || "N/A"}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EventModification;
