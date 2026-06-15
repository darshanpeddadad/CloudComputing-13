import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import axios from "axios";
import { baseUrl } from "../routes";
import { useSelector } from "react-redux";
import { toast } from "sonner";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Save, ChevronDownIcon } from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { TimePicker } from "@/components/ui/time-picker";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CreateTicketTypes = () => {
  const navigate = useNavigate();
  const { eventId } = useParams();
  const { user } = useSelector((s) => s.auth || {});

  const [ticketTypes, setTicketTypes] = useState([]);
  const [existingTicketTypes, setExistingTicketTypes] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [eventTitle, setEventTitle] = useState("");
  const [deletingIds, setDeletingIds] = useState([]);
  const [deleteConfirm, setDeleteConfirm] = useState({ open: false, ticket: null });

  useEffect(() => {
    if (!eventId) {
      toast.error("Event ID is missing");
      navigate("/events");
      return;
    }
    loadEventDetails();
    loadExistingTicketTypes();
  }, [eventId]);

  const loadEventDetails = async () => {
    try {
      const headers = {};
      if (user?.access_token) {
        headers.Authorization = `Bearer ${user.access_token}`;
      }
      const res = await axios.get(`${baseUrl}events/${eventId}`, { headers });
      const event = res.data?.data || res.data;
      setEventTitle(event.title || "Event");
    } catch (err) {
      console.error("Failed to load event:", err);
    }
  };

  const loadExistingTicketTypes = async () => {
    try {
      setLoading(true);
      const headers = {};
      if (user?.access_token) {
        headers.Authorization = `Bearer ${user.access_token}`;
      }
      const res = await axios.get(`${baseUrl}events/${eventId}/ticket-types`, {
        headers,
      });
      const data = res.data?.data || res.data || [];
      const existing = Array.isArray(data) ? data : [];
      
      const formatted = existing.map((t) => ({
        id: t.id,
        isExisting: true,
        name: t.name,
        description: t.description || "",
        price: t.price.toString(),
        currency: t.currency,
        capacity: t.capacity.toString(),
        max_per_user: t.max_per_user ? t.max_per_user.toString() : "",
        resale_allowed: t.resale_allowed,
        sale_starts_at_date: t.sale_starts_at ? format(new Date(t.sale_starts_at), "yyyy-MM-dd") : "",
        sale_starts_at_time: t.sale_starts_at ? format(new Date(t.sale_starts_at), "HH:mm") : "",
        sale_ends_at_date: t.sale_ends_at ? format(new Date(t.sale_ends_at), "yyyy-MM-dd") : "",
        sale_ends_at_time: t.sale_ends_at ? format(new Date(t.sale_ends_at), "HH:mm") : "",
      }));

      setExistingTicketTypes(formatted);
      setTicketTypes(formatted);

      if (formatted.length === 0) {
        setTicketTypes([
          {
            id: Date.now(),
            isExisting: false,
            name: "",
            description: "",
            price: "",
            currency: "USD",
            capacity: "",
            max_per_user: "",
            resale_allowed: false,
            sale_starts_at_date: "",
            sale_starts_at_time: "",
            sale_ends_at_date: "",
            sale_ends_at_time: "",
          },
        ]);
      }
    } catch (err) {
      console.error("Failed to load ticket types:", err);
      setTicketTypes([
        {
          id: Date.now(),
          isExisting: false,
          name: "",
          description: "",
          price: "",
          currency: "USD",
          capacity: "",
          max_per_user: "",
          resale_allowed: false,
          sale_starts_at_date: "",
          sale_starts_at_time: "",
          sale_ends_at_date: "",
          sale_ends_at_time: "",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const addTicketType = () => {
    setTicketTypes([
      ...ticketTypes,
      {
        id: Date.now(),
        isExisting: false,
        name: "",
        description: "",
        price: "",
        currency: "USD",
        capacity: "",
        max_per_user: "",
        resale_allowed: false,
        sale_starts_at_date: "",
        sale_starts_at_time: "",
        sale_ends_at_date: "",
        sale_ends_at_time: "",
      },
    ]);
  };

  const handleDeleteClick = (ticket) => {
    if (ticketTypes.length === 1) {
      toast.error("At least one ticket type is required");
      return;
    }

    if (!ticket.isExisting) {
      setTicketTypes(ticketTypes.filter((t) => t.id !== ticket.id));
      return;
    }

    setDeleteConfirm({ open: true, ticket });
  };

  const confirmDelete = async () => {
    const ticket = deleteConfirm.ticket;
    setDeleteConfirm({ open: false, ticket: null });

    try {
      setDeletingIds([...deletingIds, ticket.id]);
      const headers = {
        Authorization: `Bearer ${user.access_token}`,
      };
      await axios.delete(
        `${baseUrl}events/${eventId}/ticket-types/${ticket.id}`,
        { headers }
      );
      toast.success("Ticket type deleted successfully");
      setTicketTypes(ticketTypes.filter((t) => t.id !== ticket.id));
    } catch (err) {
      console.error("Failed to delete ticket type:", err);
      toast.error(
        err?.response?.data?.message || "Failed to delete ticket type"
      );
    } finally {
      setDeletingIds(deletingIds.filter((id) => id !== ticket.id));
    }
  };

  const updateTicketType = (id, field, value) => {
    setTicketTypes(
      ticketTypes.map((t) =>
        t.id === id ? { ...t, [field]: value } : t
      )
    );
  };

  const validateTicketTypes = () => {
    for (let i = 0; i < ticketTypes.length; i++) {
      const ticket = ticketTypes[i];
      if (!ticket.name.trim()) {
        return `Ticket type ${i + 1}: Name is required`;
      }
      if (!ticket.price || parseFloat(ticket.price) < 0) {
        return `Ticket type ${i + 1}: Valid price is required`;
      }
      if (!ticket.capacity || parseInt(ticket.capacity) <= 0) {
        return `Ticket type ${i + 1}: Capacity must be greater than 0`;
      }
      if (ticket.max_per_user && parseInt(ticket.max_per_user) <= 0) {
        return `Ticket type ${i + 1}: Max per user must be greater than 0`;
      }
    }
    return null;
  };

  const handleSaveAll = async () => {
    const error = validateTicketTypes();
    if (error) {
      toast.error(error);
      return;
    }

    try {
      setSaving(true);
      const headers = {
        Authorization: `Bearer ${user.access_token}`,
      };

      const promises = ticketTypes.map((ticket) => {
        let sale_starts_at = null;
        if (ticket.sale_starts_at_date && ticket.sale_starts_at_time) {
          sale_starts_at = `${ticket.sale_starts_at_date}T${ticket.sale_starts_at_time}:00`;
        }

        let sale_ends_at = null;
        if (ticket.sale_ends_at_date && ticket.sale_ends_at_time) {
          sale_ends_at = `${ticket.sale_ends_at_date}T${ticket.sale_ends_at_time}:00`;
        }

        const payload = {
          name: ticket.name,
          description: ticket.description || null,
          price: parseFloat(ticket.price),
          currency: ticket.currency,
          capacity: parseInt(ticket.capacity),
          max_per_user: ticket.max_per_user
            ? parseInt(ticket.max_per_user)
            : null,
          resale_allowed: ticket.resale_allowed,
          sale_starts_at,
          sale_ends_at,
        };

        if (ticket.isExisting) {
          return axios.patch(
            `${baseUrl}events/${eventId}/ticket-types/${ticket.id}`,
            payload,
            { headers }
          );
        } else {
          return axios.post(
            `${baseUrl}events/${eventId}/ticket-types`,
            payload,
            { headers }
          );
        }
      });

      await Promise.all(promises);
      
      const hasExisting = ticketTypes.some(t => t.isExisting);
      const hasNew = ticketTypes.some(t => !t.isExisting);
      
      if (hasExisting && hasNew) {
        toast.success("Ticket types updated and created successfully!");
      } else if (hasExisting) {
        toast.success("Ticket types updated successfully!");
      } else {
        toast.success("Ticket types created successfully!");
      }
      
      navigate(`/events/${eventId}`);
    } catch (err) {
      console.error("Failed to save ticket types:", err);
      toast.error(
        err?.response?.data?.message || "Failed to save ticket types"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    navigate(`/events/${eventId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-4"></div>
          <p className="text-muted-foreground">Loading ticket types...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold bg-linear-to-r from-primary via-secondary to-accent bg-clip-text text-transparent mb-2">
              {existingTicketTypes.length > 0 ? "Manage Ticket Types" : "Create Ticket Types"}
            </h1>
            <p className="text-muted-foreground">
              Set up ticket types for: <span className="font-semibold">{eventTitle}</span>
            </p>
          </div>

          <div className="space-y-6">
            {ticketTypes.map((ticket, index) => (
              <Card key={ticket.id} className="relative">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      Ticket Type {index + 1}
                      {ticket.isExisting && (
                        <span className="text-xs font-normal text-muted-foreground bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded-full">
                          Existing
                        </span>
                      )}
                    </CardTitle>
                    {ticketTypes.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteClick(ticket)}
                        disabled={deletingIds.includes(ticket.id)}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        {deletingIds.includes(ticket.id) ? (
                          <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent"></div>
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>
                        Name* <span className="text-xs text-muted-foreground">(e.g., Adult, VIP, Student)</span>
                      </Label>
                      <Input
                        value={ticket.name}
                        onChange={(e) =>
                          updateTicketType(ticket.id, "name", e.target.value)
                        }
                        placeholder="General Admission"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Price*</Label>
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={ticket.price}
                          onChange={(e) =>
                            updateTicketType(ticket.id, "price", e.target.value)
                          }
                          placeholder="0.00"
                          className="flex-1"
                        />
                        <Select
                          value={ticket.currency}
                          onValueChange={(value) =>
                            updateTicketType(ticket.id, "currency", value)
                          }
                        >
                          <SelectTrigger className="w-24">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="USD">USD</SelectItem>
                            <SelectItem value="EUR">EUR</SelectItem>
                            <SelectItem value="GBP">GBP</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Capacity*</Label>
                      <Input
                        type="number"
                        min="1"
                        value={ticket.capacity}
                        onChange={(e) =>
                          updateTicketType(
                            ticket.id,
                            "capacity",
                            e.target.value
                          )
                        }
                        placeholder="0"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>
                        Max Per User <span className="text-xs text-muted-foreground">(optional)</span>
                      </Label>
                      <Input
                        type="number"
                        min="1"
                        value={ticket.max_per_user}
                        onChange={(e) =>
                          updateTicketType(
                            ticket.id,
                            "max_per_user",
                            e.target.value
                          )
                        }
                        placeholder="5"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>
                      Description <span className="text-xs text-muted-foreground">(optional)</span>
                    </Label>
                    <textarea
                      value={ticket.description}
                      onChange={(e) =>
                        updateTicketType(
                          ticket.id,
                          "description",
                          e.target.value
                        )
                      }
                      className="w-full rounded-md border border-input px-3 py-2 text-sm bg-transparent text-foreground placeholder:text-muted-foreground"
                      rows={2}
                      placeholder="Describe what's included with this ticket type..."
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`resale-${ticket.id}`}
                      checked={ticket.resale_allowed}
                      onChange={(e) =>
                        updateTicketType(
                          ticket.id,
                          "resale_allowed",
                          e.target.checked
                        )
                      }
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor={`resale-${ticket.id}`} className="cursor-pointer">
                      Allow ticket resale on marketplace
                    </Label>
                  </div>

                  <div className="pt-4 border-t">
                    <Label className="text-base font-semibold mb-3 block">
                      Sale Period <span className="text-xs font-normal text-muted-foreground">(optional)</span>
                    </Label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
                      <div className="space-y-2">
                        <Label className="text-sm">Sale Starts</Label>
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <Popover>
                              <PopoverTrigger asChild>
                                <Button
                                  variant="outline"
                                  className={cn(
                                    "w-full justify-start text-left font-normal",
                                    !ticket.sale_starts_at_date && "text-muted-foreground"
                                  )}
                                >
                                  {ticket.sale_starts_at_date ? (
                                    format(new Date(ticket.sale_starts_at_date), "PPP")
                                  ) : (
                                    <span>Pick date</span>
                                  )}
                                  <ChevronDownIcon className="ml-auto h-4 w-4 opacity-50" />
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                  mode="single"
                                  selected={ticket.sale_starts_at_date ? new Date(ticket.sale_starts_at_date) : undefined}
                                  onSelect={(date) => {
                                    updateTicketType(
                                      ticket.id,
                                      "sale_starts_at_date",
                                      date ? format(date, "yyyy-MM-dd") : ""
                                    );
                                  }}
                                  initialFocus
                                />
                              </PopoverContent>
                            </Popover>
                          </div>
                          <div className="w-[140px]">
                            <TimePicker
                              value={ticket.sale_starts_at_time}
                              onChange={(time) =>
                                updateTicketType(ticket.id, "sale_starts_at_time", time)
                              }
                              placeholder="Time"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-sm">Sale Ends</Label>
                        <div className="flex gap-2">
                          <div className="flex-1">
                            <Popover>
                              <PopoverTrigger asChild>
                                <Button
                                  variant="outline"
                                  className={cn(
                                    "w-full justify-start text-left font-normal",
                                    !ticket.sale_ends_at_date && "text-muted-foreground"
                                  )}
                                >
                                  {ticket.sale_ends_at_date ? (
                                    format(new Date(ticket.sale_ends_at_date), "PPP")
                                  ) : (
                                    <span>Pick date</span>
                                  )}
                                  <ChevronDownIcon className="ml-auto h-4 w-4 opacity-50" />
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                  mode="single"
                                  selected={ticket.sale_ends_at_date ? new Date(ticket.sale_ends_at_date) : undefined}
                                  onSelect={(date) => {
                                    updateTicketType(
                                      ticket.id,
                                      "sale_ends_at_date",
                                      date ? format(date, "yyyy-MM-dd") : ""
                                    );
                                  }}
                                  initialFocus
                                />
                              </PopoverContent>
                            </Popover>
                          </div>
                          <div className="w-[140px]">
                            <TimePicker
                              value={ticket.sale_ends_at_time}
                              onChange={(time) =>
                                updateTicketType(ticket.id, "sale_ends_at_time", time)
                              }
                              placeholder="Time"
                            />
                          </div>
                        </div>
     
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Set when tickets become available for purchase and when sales end
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Button
            variant="outline"
            onClick={addTicketType}
            className="w-full mt-6 border-dashed border-2 hover:border-primary hover:bg-primary/5"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Another Ticket Type
          </Button>

          <div className="flex items-center justify-between mt-8 gap-4">
            <Button
              variant="outline"
              onClick={handleSkip}
              disabled={saving}
            >
              {existingTicketTypes.length > 0 ? "Cancel" : "Skip for Now"}
            </Button>
            <Button
              onClick={handleSaveAll}
              disabled={saving}
              className="min-w-[150px]"
            >
              {saving ? (
                <>
                  <div className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  {existingTicketTypes.length > 0 ? "Save Changes" : "Save All & Continue"}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={deleteConfirm.open}
        onOpenChange={(open) => setDeleteConfirm({ open, ticket: null })}
        onConfirm={confirmDelete}
        title="Delete Ticket Type?"
        description={`Are you sure you want to delete "${deleteConfirm.ticket?.name}"? This action cannot be undone and will affect any users who may have purchased this ticket type.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
      />
    </div>
  );
};

export default CreateTicketTypes;
