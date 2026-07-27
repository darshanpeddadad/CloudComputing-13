import { useState, useEffect } from "react";
import {
  Search,
  MessageSquare,
  User as UserIcon,
  Shield,
  ArrowLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import socketService from "@/services/socketService";

export default function ChatParticipantsList({
  activeRoom,
  currentUserId,
  onClose,
}) {
  const [participants, setParticipants] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isOrganizer, setIsOrganizer] = useState(false);

  useEffect(() => {
    if (!activeRoom) return;

    // Listen for participant updates
    const unsub = socketService.onParticipantsList((data) => {
      if (
        data.room_id === activeRoom.id ||
        data.event_id === activeRoom.event_id
      ) {
        setParticipants(data.participants || []);

        // Check if user is organizer
        const me = data.participants.find((p) => p.user_id === currentUserId);
        if (me && me.role === "owner") {
          setIsOrganizer(true);
        } else if (activeRoom.context?.includes("admin")) {
          setIsOrganizer(true);
        }
      }
    });

    return () => unsub();
  }, [activeRoom, currentUserId]);

  // Check initial list
  useEffect(() => {
    if (activeRoom?.participants) {
      setParticipants(activeRoom.participants);
      const me = activeRoom.participants.find(
        (p) => p.user_id === currentUserId
      );
      if (me && me.role === "owner") setIsOrganizer(true);
    }
  }, [activeRoom, currentUserId]);

  const filteredParticipants = participants.filter((p) => {
    if (p.user_id === currentUserId) return false;
    if (!searchQuery) return true;
    const name = p.name || p.user?.first_names || "Unknown";
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleDataMessage = (targetId) => {
    const eventId = socketService.getEventId(activeRoom);

    if (eventId) {
      socketService.joinDirect(targetId, eventId);
      onClose();
    }
  };

  return (
    <div className="absolute inset-0 bg-background z-20 flex flex-col animate-in slide-in-from-right-10 duration-200">
      <div className="p-3 border-b flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 hover:bg-muted"
          onClick={onClose}
        >
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <span className="font-semibold text-sm">
          Participants ({participants.length})
        </span>
      </div>

      <div className="p-3 border-b bg-muted/20">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search people..."
            className="pl-9 h-9 bg-background"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <ScrollArea className="flex-1 p-0">
        {filteredParticipants.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-muted-foreground text-sm">
            No participants found.
          </div>
        ) : (
          <div className="flex flex-col">
            {filteredParticipants.map((p) => (
              <div
                key={p.user_id}
                className="flex items-center justify-between p-3 hover:bg-muted/50 transition-colors border-b last:border-0 border-muted/20"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm shrink-0">
                    {(p.name || p.user?.first_names || "?")[0]?.toUpperCase()}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm font-medium truncate">
                      {p.name || p.user?.first_names || "User"}
                    </span>
                    {p.role === "owner" && (
                      <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full w-fit flex items-center gap-0.5 mt-0.5">
                        Organizer
                      </span>
                    )}
                  </div>
                </div>

                {(isOrganizer || p.role === "owner") &&
                  p.user_id !== currentUserId && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => handleDataMessage(p.user_id)}
                      title="Message"
                    >
                      <MessageSquare className="h-4 w-4 text-muted-foreground hover:text-primary" />
                    </Button>
                  )}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
