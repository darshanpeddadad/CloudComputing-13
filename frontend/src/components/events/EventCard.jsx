import React from "react";
import { Link } from "react-router";
import { Card, CardHeader, CardTitle, CardDescription } from "../ui/card";
import { CheckCircle2, Clock, MapPin, Tag } from "lucide-react";

const EventCard = ({ event }) => {
  //check if the event url start from https://gdsd2025.s3.eu-central-1.amazonaws.com/images/ if not use default image
  const image = event.images && event.images[0];

  const start =
    event.start_date || event.start
      ? new Date(event.start_date || event.start).toLocaleDateString()
      : null;

  const categoryLabel =
    typeof event.category === "string"
      ? event.category
      : event.category && typeof event.category === "object"
      ? event.category.name || event.category.title || "General"
      : "General";

  const description =
    event.short_description ||
    event.description ||
    event.summary ||
    "No description available.";

  const completionDateRaw =
    event.end_date || event.end || event.start_date || event.start;
  const completionDate = completionDateRaw ? new Date(completionDateRaw) : null;
  const isCompleted =
    completionDate instanceof Date &&
    !Number.isNaN(completionDate.getTime()) &&
    completionDate.getTime() < Date.now();

  const borderColors = [
    "border-primary/30",
    "border-secondary/30",
    "border-accent/30",
  ];
  const borderColor = borderColors[event.id % 3];

  return (
    <Link to={`/events/${event.id}`}>
      <Card
        className={`overflow-hidden hover:shadow-lg transition-all hover:scale-[1] cursor-pointer h-full ${borderColor} border-2 group !pt-0 !gap-0`}
      >
        <div className="aspect-video overflow-hidden relative">
          <img
            src={image}
            alt={event.title}
            className="w-full h-full object-cover object-center block"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />

          <div className="absolute top-4 left-4 bg-white/90 dark:bg-card/90 backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider shadow-lg flex items-center gap-1.5">
            <Tag className="w-3 h-3 text-primary" />
            {categoryLabel}
          </div>

          {isCompleted && (
            <div className="absolute top-4 right-4 bg-amber-500/95 text-white backdrop-blur-sm px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider shadow-lg flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3" />
              Completed
            </div>
          )}
        </div>

        <CardHeader className="mt-4">
          <CardTitle className="text-xl line-clamp-2 group-hover:text-primary transition-colors">
            {event.title}
          </CardTitle>
          <CardDescription className="space-y-3 mt-3">
            {start && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-primary" />
                <span>{start}</span>
              </div>
            )}

            {event.location && (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="w-4 h-4 text-secondary" />
                <span className="line-clamp-1">{event.location}</span>
              </div>
            )}

            <p className="text-sm line-clamp-2 mt-2">{description}</p>
          </CardDescription>
        </CardHeader>
      </Card>
    </Link>
  );
};

export default EventCard;
