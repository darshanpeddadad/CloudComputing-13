import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import axios from "axios";
import { baseUrl } from "../routes";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { ChevronDownIcon } from "lucide-react";
import { useSelector } from "react-redux";
import LocationPicker from "@/components/events/LocationPicker";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { TimePicker } from "@/components/ui/time-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const normalizeTime = (value) => {
  if (!value) return "";
  const parts = String(value).split(":");
  if (parts.length >= 2) {
    return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}`;
  }
  return String(value);
};

const EditEvent = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const eventId = id;
  const { user } = useSelector((s) => s.auth || {});

  const [form, setForm] = useState({
    title: "",
    description: "",
    location: "",
    latitude: "",
    longitude: "",
    category_id: "",
    start_date: "",
    end_date: "",
    start_time: "",
    end_time: "",
    max_attendees: "",
  });

  const [loading, setLoading] = useState(false);
  const [eventLoading, setEventLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [catsLoading, setCatsLoading] = useState(false);
  const [catsError, setCatsError] = useState(null);
  const [isStartDateOpen, setIsStartDateOpen] = useState(false);
  const [isEndDateOpen, setIsEndDateOpen] = useState(false);

  const handleChange = (k) => (e) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const validate = () => {
    if (!form.title.trim()) return "Title is required";
    if (!form.location.trim()) return "Location is required";
    if (!form.latitude || !form.longitude) return "Please select Location on Map";
    if (!form.start_date) return "Start date is required";
    if (!form.end_date) return "End date is required";
    if (!form.start_time) return "Start time of event is required";
    if (!form.end_time) return "End time of event is required";

    const startDate = new Date(form.start_date);
    const endDate = new Date(form.end_date);

    if (endDate < startDate) {
      return "End date cannot be earlier than start date";
    }

    if (form.start_date === form.end_date && form.start_time && form.end_time) {
      if (form.end_time <= form.start_time) {
        return "End time must be after start time";
      }
    }

    if (!form.category_id) return "Category is required";

    const maxAttendees = Number(form.max_attendees);
    if (!maxAttendees || maxAttendees <= 0) {
      return "Max attendees must be greater than 0";
    }

    return null;
  };

  useEffect(() => {
    if (!eventId) return;

    setEventLoading(true);
    const headers = {};
    if (user?.access_token) {
      headers.Authorization = `Bearer ${user.access_token}`;
    }

    axios
      .get(`${baseUrl}events/${eventId}`, { headers })
      .then((res) => {
        const event = res.data?.data;
        if (!event) {
          throw new Error("Event not found");
        }
        setForm((prev) => ({
          ...prev,
          title: event.title || "",
          description: event.description || "",
          location: event.location || "",
          latitude: event.latitude ?? "",
          longitude: event.longitude ?? "",
          category_id: event.category?.id || "",
          start_date: event.start_date || "",
          end_date: event.end_date || "",
          start_time: normalizeTime(event.start_time),
          end_time: normalizeTime(event.end_time),
          max_attendees: event.max_attendees ?? "",
        }));
      })
      .catch((err) => {
        console.error("Failed to load event:", err);
        toast.error("Failed to load event");
      })
      .finally(() => setEventLoading(false));
  }, [eventId, user?.access_token]);

  useEffect(() => {
    const loadCategories = async () => {
      if (!user?.access_token) return;
      setCatsLoading(true);
      setCatsError(null);
      try {
        const res = await axios.get(`${baseUrl}categories/`, {
          headers: { Authorization: `Bearer ${user.access_token}` },
        });
        const payload = res.data;
        let categoryList = [];
        if (Array.isArray(payload)) {
          categoryList = payload;
        } else if (Array.isArray(payload?.data)) {
          categoryList = payload.data;
        } else if (payload?.data) {
          categoryList = [payload.data];
        }

        setCategories(categoryList);
        if (!form.category_id && categoryList.length > 0) {
          setForm((s) => ({ ...s, category_id: categoryList[0].id }));
        }
      } catch (err) {
        console.error("Failed to load categories:", err);
        setCatsError("Failed to load categories");
      } finally {
        setCatsLoading(false);
      }
    };

    loadCategories();
  }, [user?.access_token, form.category_id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }

    const editData = {
      title: form.title,
      description: form.description,
      location: form.location,
      latitude: Number(form.latitude),
      longitude: Number(form.longitude),
      category_id: form.category_id,
      start_date: form.start_date,
      end_date: form.end_date,
      start_time: form.start_time || "00:00",
      end_time: form.end_time || "23:59",
      max_attendees: Number(form.max_attendees),
    };

    try {
      setLoading(true);
      const headers = {};
      if (user?.access_token) {
        headers.Authorization = `Bearer ${user.access_token}`;
      }
      await axios.post(`${baseUrl}events/${eventId}/edit-requests`, editData, { headers });
      toast.success("Edit request submitted for review.");
      navigate("/user/dashboard");
    } catch (submitErr) {
      console.error(submitErr);
      toast.error(
        submitErr?.response?.data?.detail ||
          submitErr?.response?.data?.message ||
          submitErr.message ||
          "Failed to submit edit request"
      );
    } finally {
      setLoading(false);
    }
  };

  if (eventLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-10 flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <Card className="max-w-3xl mx-auto">
          <CardHeader>
            <CardTitle>Edit Event</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Title*</Label>
                <Input value={form.title} onChange={handleChange("title")} />
              </div>

              <div className="space-y-2">
                <Label>Description*</Label>
                <textarea
                  value={form.description}
                  onChange={handleChange("description")}
                  className="w-full rounded-md border border-input px-3 py-2 text-base bg-transparent text-foreground placeholder:text-muted-foreground"
                  rows={6}
                />
              </div>

              <div className="grid grid-cols-1 gap-3">
                <div className="space-y-2">
                  <Label>Location*</Label>
                  <Input value={form.location} onChange={handleChange("location")} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Select Location on Map*</Label>
                <LocationPicker
                  lat={form.latitude ? Number(form.latitude) : null}
                  lng={form.longitude ? Number(form.longitude) : null}
                  onChange={({ lat, lng }) => {
                    setForm((p) => ({ ...p, latitude: lat, longitude: lng }));
                  }}
                />
                <div className="text-sm text-muted-foreground mt-2">
                  {form.latitude && form.longitude
                    ? `Selected: ${form.latitude}, ${form.longitude}`
                    : "Click on the map to select location"}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Start Date*</Label>
                  <Popover open={isStartDateOpen} onOpenChange={setIsStartDateOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full justify-between text-left font-normal",
                          !form.start_date && "text-muted-foreground"
                        )}
                      >
                        {form.start_date ? (
                          format(new Date(form.start_date), "PPP")
                        ) : (
                          <span>Pick start date</span>
                        )}
                        <ChevronDownIcon className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={form.start_date ? new Date(form.start_date) : undefined}
                        onSelect={(date) => {
                          setForm((p) => ({
                            ...p,
                            start_date: date ? format(date, "yyyy-MM-dd") : "",
                          }));
                          setIsStartDateOpen(false);
                        }}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div className="space-y-2">
                  <Label>End Date*</Label>
                  <Popover open={isEndDateOpen} onOpenChange={setIsEndDateOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full justify-between text-left font-normal",
                          !form.end_date && "text-muted-foreground"
                        )}
                      >
                        {form.end_date ? (
                          format(new Date(form.end_date), "PPP")
                        ) : (
                          <span>Pick end date</span>
                        )}
                        <ChevronDownIcon className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={form.end_date ? new Date(form.end_date) : undefined}
                        onSelect={(date) => {
                          setForm((p) => ({
                            ...p,
                            end_date: date ? format(date, "yyyy-MM-dd") : "",
                          }));
                          setIsEndDateOpen(false);
                        }}
                        initialFocus
                        disabled={(date) => {
                          if (form.start_date) {
                            const startDate = new Date(form.start_date);
                            startDate.setHours(0, 0, 0, 0);
                            const checkDate = new Date(date);
                            checkDate.setHours(0, 0, 0, 0);
                            return checkDate < startDate;
                          }
                          return false;
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Start Time*</Label>
                  <TimePicker
                    value={form.start_time}
                    onChange={(time) => setForm((p) => ({ ...p, start_time: time }))}
                    placeholder="Pick start time"
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Time*</Label>
                  <TimePicker
                    value={form.end_time}
                    onChange={(time) => setForm((p) => ({ ...p, end_time: time }))}
                    placeholder="Pick end time"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Max Attendees*</Label>
                  <Input
                    value={form.max_attendees}
                    onChange={handleChange("max_attendees")}
                    type="number"
                    min={1}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Category*</Label>
                  {catsLoading ? (
                    <div className="text-sm text-muted-foreground">
                      Loading categories…
                    </div>
                  ) : catsError ? (
                    <div className="text-sm text-destructive">{catsError}</div>
                  ) : (
                    <Select
                      value={form.category_id}
                      onValueChange={(value) =>
                        setForm((s) => ({ ...s, category_id: value }))
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </div>

              <CardFooter>
                <div className="ml-auto">
                  <Button type="submit" disabled={loading}>
                    {loading ? "Submitting…" : "Submit Edit Request"}
                  </Button>
                </div>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EditEvent;
