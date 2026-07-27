import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Users, Shield, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import chatApiService from "@/services/chatApiService";
import socketService from "@/services/socketService";
import { useSelector } from "react-redux";

export default function RoomList({ rooms, onSelect, currentUserId }) {
  const [showSupport, setShowSupport] = useState(false);
  const [admins, setAdmins] = useState([]);
  const [loadingAdmins, setLoadingAdmins] = useState(false);

  const { user } = useSelector((state) => state.auth);
  const isAdmin =
    user?.user?.roles?.includes("admin") || user?.roles?.includes("admin");

  const handleOpenSupport = async () => {
    setShowSupport(true);
    if (admins.length === 0) {
      setLoadingAdmins(true);
      try {
        const data = await chatApiService.fetchAdmins();
        setAdmins(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingAdmins(false);
      }
    }
  };

  const handleContactAdmin = (adminId) => {
    // Join direct chat with admin
    socketService.joinDirect(adminId, null);
  };

  if (showSupport) {
    return (
      <div className="flex flex-col h-full min-h-0 bg-background animate-in slide-in-from-right duration-200">
        <div className="p-3 border-b flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 hover:bg-muted"
            onClick={() => setShowSupport(false)}
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <span className="font-semibold text-sm">Contact Support</span>
        </div>
        <ScrollArea className="flex-1 min-h-0">
          {loadingAdmins ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2"></div>
              <p className="text-xs">Loading support agents...</p>
            </div>
          ) : admins.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No support agents available.
            </div>
          ) : (
            <div className="divide-y">
              {admins.map((admin) => (
                <div
                  key={admin.id}
                  className="flex items-center justify-between p-3 hover:bg-muted/50 transition-colors border-b last:border-0 border-muted/20"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold text-sm shrink-0">
                      {admin.first_names?.[0]?.toUpperCase() || "A"}
                    </div>
                    <div className="flex flex-col min-w-0">
                      <span className="text-sm font-medium truncate">
                        {admin.first_names} {admin.last_name}
                      </span>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0"
                    onClick={() => handleContactAdmin(admin.id)}
                    title="Message"
                  >
                    <MessageSquare className="h-4 w-4 text-muted-foreground hover:text-primary" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full min-h-0 bg-background animate-in slide-in-from-left duration-200">
      {/* Support Button - Visible only to users */}
      {!isAdmin && (
        <div className="p-3 border-b">
          <Button
            variant="outline"
            className="w-full gap-2 border-dashed border-primary/30 hover:bg-primary/5 hover:text-primary transition-all"
            onClick={handleOpenSupport}
          >
            <Shield className="w-4 h-4" />
            Contact Support
          </Button>
        </div>
      )}

      <ScrollArea className="flex-1 min-h-0">
        {!rooms || rooms.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground space-y-4">
            <div className="h-12 w-12 bg-muted rounded-full flex items-center justify-center">
              <MessageSquare className="h-6 w-6 opacity-30" />
            </div>
            <div>
              <p className="text-sm font-medium">No active chats</p>
              <p className="text-xs opacity-70 mt-1 max-w-[200px]">
                Join an event or contact support to start chatting.
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y text-left">
            {rooms.map((room, i) => {
              const isGroup =
                room.room_type === "event_group" || room.type === "event_group";

              let title = room.title;
              if (!isGroup) {
                if (
                  room.other_user?.name &&
                  room.other_user.id !== currentUserId
                ) {
                  title = room.other_user.name;
                } else {
                  const other = room.participants?.find(
                    (p) => p.user_id !== currentUserId
                  );
                  if (other?.name) title = other.name;
                }
              }
              if (!title) title = isGroup ? "Event Group" : "Direct Chat";
              const lastMsg = room.last_message?.content || "No messages yet";
              const date = room.last_message?.sent_at
                ? new Date(room.last_message.sent_at).toLocaleDateString()
                : "";

              return (
                <button
                  key={room.id || i}
                  onClick={() => onSelect(room)}
                  className="w-full p-4 flex gap-3 text-left hover:bg-accent/50 transition-all duration-200 group"
                >
                  <div className="h-10 w-10 bg-primary/10 text-primary rounded-full flex items-center justify-center shrink-0 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    {isGroup ? (
                      <Users className="h-5 w-5" />
                    ) : (
                      <MessageSquare className="h-5 w-5" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <div className="flex justify-between items-center mb-0.5">
                      <span className="font-semibold text-sm truncate">
                        {title}
                      </span>
                      <div className="flex items-center gap-2">
                        {date && (
                          <span className="text-[10px] text-muted-foreground shrink-0">
                            {date}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex justify-between items-end">
                      <span className="text-xs text-muted-foreground truncate block max-w-[180px]">
                        {lastMsg}
                      </span>
                      {room.unread_count > 0 && (
                        <span className="flex items-center justify-center min-w-[18px] h-[18px] px-1 bg-red-500 text-white text-[10px] font-bold rounded-full ml-1">
                          {room.unread_count}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
