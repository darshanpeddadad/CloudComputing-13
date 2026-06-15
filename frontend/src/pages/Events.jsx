import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import EventCard from "../components/events/EventCard";
import { baseUrl } from "../routes";
import { Pagination, PaginationInfo } from "../components/ui/pagination";
import { useSelector } from "react-redux";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CalendarRange,
  MapPin,
  SlidersHorizontal,
  Users,
  X,
} from "lucide-react";

const DEFAULT_FILTERS = {
  category: "all",
  timeFilter: "all",
  sortBy: "start_date_desc",
  location: "",
  startDateFrom: "",
  startDateTo: "",
  minAttendees: "",
  maxAttendees: "",
  useSemanticSearch: false,
};

const SORT_OPTIONS = [
  { value: "start_date_desc", label: "Latest first" },
  { value: "title_asc", label: "Title A-Z" },
  { value: "title_desc", label: "Title Z-A" },
  { value: "max_attendees_desc", label: "Capacity high-low" },
  { value: "max_attendees_asc", label: "Capacity low-high" },
];

const TIME_FILTER_OPTIONS = [
  { value: "all", label: "Any time" },
  { value: "upcoming", label: "Upcoming" },
  { value: "ongoing", label: "Ongoing" },
  { value: "past", label: "Past" },
];

const Events = () => {
  const { user } = useSelector((s) => s.auth || {});
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState([]);
  const [categoriesLoading, setCategoriesLoading] = useState(false);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [pendingSearch, setPendingSearch] = useState("");

  const [recommendedEvents, setRecommendedEvents] = useState([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [recommendationError, setRecommendationError] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(9);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 9,
    total: 0,
    pages: 0,
    has_next: false,
  });

  const activeFilterCount =
    (search ? 1 : 0) +
    (filters.category !== "all" ? 1 : 0) +
    (filters.timeFilter !== "all" ? 1 : 0) +
    (filters.sortBy !== "start_date_desc" ? 1 : 0) +
    (filters.location ? 1 : 0) +
    (filters.startDateFrom ? 1 : 0) +
    (filters.startDateTo ? 1 : 0) +
    (filters.minAttendees ? 1 : 0) +
    (filters.maxAttendees ? 1 : 0) +
    (filters.useSemanticSearch ? 1 : 0);

  const fetchEvents = useCallback(
    async (page = 1, searchTerm = "", nextFilters = DEFAULT_FILTERS) => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          page,
          page_size: pageSize,
          sort_by: nextFilters.sortBy,
        };

        const trimmedSearch = searchTerm.trim();
        const trimmedLocation = nextFilters.location.trim();

        if (trimmedSearch) params.search = trimmedSearch;
        if (nextFilters.category !== "all")
          params.category = nextFilters.category;
        if (nextFilters.timeFilter !== "all")
          params.time_filter = nextFilters.timeFilter;
        if (trimmedLocation) params.location = trimmedLocation;
        if (nextFilters.startDateFrom)
          params.start_date_from = nextFilters.startDateFrom;
        if (nextFilters.startDateTo)
          params.start_date_to = nextFilters.startDateTo;

        const minAttendees = Number.parseInt(nextFilters.minAttendees, 10);
        const maxAttendees = Number.parseInt(nextFilters.maxAttendees, 10);

        if (Number.isInteger(minAttendees) && minAttendees > 0) {
          params.min_attendees = minAttendees;
        }
        if (Number.isInteger(maxAttendees) && maxAttendees > 0) {
          params.max_attendees = maxAttendees;
        }

        if (nextFilters.useSemanticSearch) {
          params.use_semantic_search = true;
        }

        const res = await axios.get(`${baseUrl}events/`, { params });
        const payload = res.data;

        let items = [];
        let paginationData = null;

        if (payload?.data) {
          items = payload.data.items || [];
          paginationData = payload.data.pagination;
        } else if (Array.isArray(payload)) {
          items = payload;
        }

        setEvents(items);

        if (paginationData) {
          setPagination(paginationData);
        }
      } catch (err) {
        setError(err.message || "Failed to load events");
      } finally {
        setLoading(false);
      }
    },
    [pageSize],
  );

  const fetchCategories = useCallback(async () => {
    if (!user?.access_token) {
      setCategories(["All"]);
      return;
    }

    try {
      setCategoriesLoading(true);
      const headers = {
        Authorization: `Bearer ${user.access_token}`,
      };

      const res = await axios.get(`${baseUrl}categories/`, { headers });
      const payload = res.data;

      let categoryList = [];
      if (Array.isArray(payload)) {
        categoryList = payload;
      } else if (Array.isArray(payload?.data)) {
        categoryList = payload.data;
      } else if (payload?.data) {
        categoryList = [payload.data];
      }

      const categoryNames = categoryList.map(
        (cat) => cat.name || cat.title || cat,
      );
      setCategories(categoryNames.sort());
    } catch (err) {
      console.error("Failed to load categories:", err);
      setCategories([]);
    } finally {
      setCategoriesLoading(false);
    }
  }, [user?.access_token]);

  const fetchRecommendations = useCallback(async () => {
    if (!user?.access_token) {
      setRecommendedEvents([]);
      return;
    }

    try {
      setLoadingRecommendations(true);
      setRecommendationError(null);
      const headers = { Authorization: `Bearer ${user.access_token}` };
      const res = await axios.get(`${baseUrl}events/recommendations`, { headers });
      const payload = res.data;

      let items = [];
      if (payload?.data) {
        items = payload.data.items || [];
      } else if (Array.isArray(payload)) {
        items = payload;
      }
      setRecommendedEvents(items);
    } catch (err) {
      console.error("Failed to load recommendations:", err);
      setRecommendationError(err.message || "Failed to load recommendations");
    } finally {
      setLoadingRecommendations(false);
    }
  }, [user?.access_token]);

  useEffect(() => {
    fetchEvents(currentPage, search, filters);
  }, [fetchEvents, currentPage, search, filters]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (pendingSearch !== search) {
        setSearch(pendingSearch);
        setCurrentPage(1);
      }
    }, 500);
    return () => clearTimeout(t);
  }, [pendingSearch, search]);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const clearAllFilters = () => {
    setPendingSearch("");
    setSearch("");
    setFilters(DEFAULT_FILTERS);
    setCurrentPage(1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/50">
      <div className="container mx-auto px-4 py-12">
        <div className="mb-10 space-y-5">
          <div className="rounded-2xl border border-primary/20 bg-white/80 dark:bg-card/80 backdrop-blur-sm shadow-md p-4 md:p-5">
            <div className="flex flex-col lg:flex-row gap-3">
              <div className="flex-1 space-y-2">
                <label htmlFor="search" className="sr-only">
                  Search events
                </label>
                <Input
                  id="search"
                  type="search"
                  value={pendingSearch}
                  onChange={(e) => setPendingSearch(e.target.value)}
                  placeholder="Search by title or description"
                  className="h-11 bg-white/85 dark:bg-background/60"
                />
                <div className="flex items-center space-x-2 pt-1 pl-1">
                  <Switch
                    id="semantic-search"
                    checked={filters.useSemanticSearch}
                    onCheckedChange={(checked) =>
                      handleFilterChange("useSemanticSearch", checked)
                    }
                  />
                  <Label htmlFor="semantic-search" className="text-sm font-medium text-muted-foreground cursor-pointer transition-colors hover:text-foreground">AI Smart Search</Label>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:w-[620px]">
                <Select
                  value={filters.category}
                  onValueChange={(value) =>
                    handleFilterChange("category", value)
                  }
                  disabled={categoriesLoading}
                >
                  <SelectTrigger className="w-full h-11 bg-white/85 dark:bg-background/60">
                    <SelectValue
                      placeholder={
                        categoriesLoading ? "Loading..." : "Category"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All categories</SelectItem>
                    {categories.map((categoryName) => (
                      <SelectItem key={categoryName} value={categoryName}>
                        {categoryName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={filters.timeFilter}
                  onValueChange={(value) =>
                    handleFilterChange("timeFilter", value)
                  }
                >
                  <SelectTrigger className="w-full h-11 bg-white/85 dark:bg-background/60">
                    <SelectValue placeholder="Time" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIME_FILTER_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={filters.sortBy}
                  onValueChange={(value) => handleFilterChange("sortBy", value)}
                >
                  <SelectTrigger className="w-full h-11 bg-white/85 dark:bg-background/60">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    {SORT_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mt-4 pt-4 border-t border-border/60">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge
                  variant="outline"
                  className="border-primary/40 text-primary"
                >
                  {activeFilterCount} active{" "}
                  {activeFilterCount === 1 ? "filter" : "filters"}
                </Badge>
                {filters.timeFilter !== "all" && (
                  <Badge variant="secondary" className="gap-1">
                    <CalendarRange className="h-3 w-3" />
                    {
                      TIME_FILTER_OPTIONS.find(
                        (option) => option.value === filters.timeFilter,
                      )?.label
                    }
                  </Badge>
                )}
                {filters.location && (
                  <Badge variant="secondary" className="gap-1">
                    <MapPin className="h-3 w-3" />
                    {filters.location}
                  </Badge>
                )}
                {(filters.minAttendees || filters.maxAttendees) && (
                  <Badge variant="secondary" className="gap-1">
                    <Users className="h-3 w-3" />
                    Capacity range
                  </Badge>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAdvancedOpen((prev) => !prev)}
                  className="bg-white/70 dark:bg-background/50"
                >
                  <SlidersHorizontal className="h-4 w-4" />
                  {advancedOpen ? "Hide advanced" : "Advanced filters"}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={clearAllFilters}
                  disabled={activeFilterCount === 0}
                >
                  <X className="h-4 w-4" />
                  Clear all
                </Button>
              </div>
            </div>

            {advancedOpen && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3 bg-background/70 rounded-xl border border-border p-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Location
                  </label>
                  <Input
                    value={filters.location}
                    onChange={(e) =>
                      handleFilterChange("location", e.target.value)
                    }
                    placeholder="e.g. Fulda Campus"
                    className="bg-white/90 dark:bg-background"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Start date from
                  </label>
                  <Input
                    type="date"
                    value={filters.startDateFrom}
                    onChange={(e) =>
                      handleFilterChange("startDateFrom", e.target.value)
                    }
                    className="bg-white/90 dark:bg-background"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Start date to
                  </label>
                  <Input
                    type="date"
                    value={filters.startDateTo}
                    onChange={(e) =>
                      handleFilterChange("startDateTo", e.target.value)
                    }
                    className="bg-white/90 dark:bg-background"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Min capacity
                  </label>
                  <Input
                    type="number"
                    min={1}
                    value={filters.minAttendees}
                    onChange={(e) =>
                      handleFilterChange("minAttendees", e.target.value)
                    }
                    placeholder="e.g. 50"
                    className="bg-white/90 dark:bg-background"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-muted-foreground">
                    Max capacity
                  </label>
                  <Input
                    type="number"
                    min={1}
                    value={filters.maxAttendees}
                    onChange={(e) =>
                      handleFilterChange("maxAttendees", e.target.value)
                    }
                    placeholder="e.g. 500"
                    className="bg-white/90 dark:bg-background"
                  />
                </div>

              </div>
            )}
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent"></div>
          </div>
        )}

        {error && (
          <div className="mt-4 text-destructive text-center py-8">{error}</div>
        )}

        {!loading && !error && events.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg">No events found.</p>
            {activeFilterCount > 0 && (
              <p className="text-sm text-muted-foreground mt-2">
                Try adjusting your search or filters
              </p>
            )}
          </div>
        )}

        {!loading && !error && events.length > 0 && (
          <>
            {user?.access_token && activeFilterCount === 0 && (
              <div className="mb-12 pb-12 border-b border-border/60 min-h-[300px]">
                <div className="flex items-center gap-3 mb-6">
                  <h2 className="text-2xl font-bold tracking-tight text-primary">
                    Recommended for You
                  </h2>
                  <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20 transition-colors">
                    Top Picks
                  </Badge>
                </div>
                {loadingRecommendations ? (
                  <div className="flex justify-center items-center py-12">
                     <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : recommendationError ? (
                  <div className="text-destructive text-sm py-4">{recommendationError}</div>
                ) : recommendedEvents.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {recommendedEvents.slice(0, 3).map((ev) => (
                      <EventCard key={`rec-${ev.id}`} event={ev} />
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground py-4">No recommendations at this time.</p>
                )}
              </div>
            )}

            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
              <h2 className="text-2xl font-bold tracking-tight">
                {activeFilterCount > 0 ? "Search Results" : "All Events"}
              </h2>
              <PaginationInfo
                currentPage={pagination.page}
                pageSize={pagination.page_size}
                total={pagination.total}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map((ev) => (
                <EventCard key={ev.id} event={ev} />
              ))}
            </div>

            {pagination.pages > 1 && (
              <div className="mt-12">
                <Pagination
                  currentPage={pagination.page}
                  totalPages={pagination.pages}
                  hasNext={pagination.has_next}
                  hasPrev={pagination.page > 1}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Events;
