import { useState, useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { Send, Loader2, Users, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

import socketService from "@/services/socketService";
import chatApiService from "@/services/chatApiService";
import sosApiService from "@/services/sosApiService";
import { toast } from "sonner";
import ChatParticipantsList from "./ChatParticipantsList";

export default function ChatRoomView({ activeRoom }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isJoined, setIsJoined] = useState(false);
  const [connectedSocketRoomId, setConnectedSocketRoomId] = useState(null);
  const [error, setError] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [showParticipants, setShowParticipants] = useState(false);
  const [sendingSOS, setSendingSOS] = useState(false);
  const [sosDialogOpen, setSosDialogOpen] = useState(false);
  const [sosMessage, setSosMessage] = useState("");

  const messagesEndRef = useRef(null);
  const authState = useSelector((state) => state.auth || {});
  const currentUser = authState.user?.user;
  const currentUserId = currentUser?.id;

  useEffect(() => {
    // Reset State
    setMessages([]);
    setIsJoined(false);
    setError(null);
    setIsReadOnly(false);
    setSendingSOS(false);
    setSosDialogOpen(false);
    setSosMessage("");

    // Load History
    if (activeRoom.id) {
      chatApiService
        .fetchHistory(activeRoom.id)
        .then((data) => {
          setMessages(data.reverse());
          if (data.length > 0) {
            chatApiService.markRead(activeRoom.id, data[data.length - 1].id);
          }
        })
        .catch((err) => { });
    }

    // Join Room
    socketService.joinRoom(activeRoom, currentUserId);

    // Event Listeners
    const unsubJoin = socketService.onAnyJoin((data) => {
      const eventId = socketService.getEventId(activeRoom);

      // Match received room to current room
      const isMatch =
        (data.chat_room_id && data.chat_room_id === activeRoom.id) ||
        data.room_id === activeRoom.id ||
        (data.event_id && data.event_id === eventId);

      if (isMatch) {
        setIsJoined(true);
        setConnectedSocketRoomId(data.room_id);
        setError(null);
      }
    });

    const unsubMsg = socketService.onAnyMessage((data) => {
      // Read Receipt
      if (data.id && activeRoom.id)
        chatApiService.markRead(activeRoom.id, data.id);

      if (data.sender_id === currentUserId) return;
      setMessages((prev) => [...prev, data]);
      scrollToBottom();
    });

    const unsubErr = socketService.onAnyError((data) => {
      const errMsg = data.message || "Connection error";
      if (errMsg.includes("Event has ended")) {
        setIsReadOnly(true);
        setError("This event has ended. Chat is read-only.");
      } else {
        setError(errMsg);
      }
    });

    return () => {
      unsubJoin();
      unsubMsg();
      unsubErr();
      if (activeRoom.id) socketService.leaveRoom(activeRoom.id);
    };
  }, [activeRoom.id, activeRoom.event_id, activeRoom.context, currentUserId]);

  const scrollToBottom = () => {
    setTimeout(
      () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }),
      100
    );
  };

  useEffect(() => scrollToBottom(), [messages]);

  const getSenderName = (msg) => {
    if (msg.sender_name) return msg.sender_name;
    if (msg.sender?.name) return msg.sender.name;

    const sId = msg.sender_id;
    if (!sId) return "Unknown";

    if (activeRoom.other_user?.id === sId) return activeRoom.other_user.name;

    const participant = activeRoom.participants?.find((p) => p.user_id === sId);
    if (participant?.name) return participant.name;

    // fallback
    const historyMsg = messages.find(
      (m) => m.sender_id === sId && m.sender?.name
    );
    return historyMsg ? historyMsg.sender.name : sId.slice(0, 8);
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || !isJoined || isReadOnly) return;

    const content = inputValue.trim();

    // Send
    socketService.sendMessage(activeRoom, content, connectedSocketRoomId);

    // Optimistic Update
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        content: content,
        sender_id: currentUserId,
        sender_name: currentUser
          ? `${currentUser.first_names} ${currentUser.last_name || ""}`
          : "You",
        sent_at: new Date().toISOString(),
        isSelf: true,
      },
    ]);
    setInputValue("");
  };

  const handleSOS = (customMessage = null) => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser");
      return;
    }

    const eventId = socketService.getEventId(activeRoom) || activeRoom.event_id;
    if (!eventId) {
      toast.error("Could not determine event context for SOS");
      return;
    }

    setSendingSOS(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          await sosApiService.triggerSOS({
            event_id: eventId,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            message: customMessage || "Emergency Alert",
          });
          toast.success("SOS Alert sent! Help is on the way.");
          setSosDialogOpen(false);
          setSosMessage("");
        } catch (error) {
          toast.error(
            "Failed to send SOS: " + (error.response?.data?.detail || error.message)
          );
        } finally {
          setSendingSOS(false);
        }
      },
      (error) => {
        setSendingSOS(false);
        let msg = "An unknown error occurred.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            msg = "Location permission denied. Please enable location services.";
            break;
          case error.POSITION_UNAVAILABLE:
            msg = "Location information is unavailable.";
            break;
          case error.TIMEOUT:
            msg = "Location request timed out.";
            break;
        }
        toast.error(msg);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  const isGroup =
    activeRoom.room_type === "event_group" || activeRoom.type === "event_group";

  return (
    <div className="flex flex-col h-full relative">
      {/* Participants List for Group Chat */}
      {isGroup && showParticipants && (
        <ChatParticipantsList
          activeRoom={activeRoom}
          currentUserId={currentUserId}
          onClose={() => setShowParticipants(false)}
        />
      )}

      {/* Header Buttons */}
      {isGroup && isJoined && !showParticipants && (
        <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
          <Button
            variant="destructive"
            size="sm"
            className="h-8 shadow-sm text-xs gap-1.5 px-3 rounded-full animate-in fade-in"
            onClick={() => setSosDialogOpen(true)}
            disabled={sendingSOS}
          >
            {sendingSOS ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <AlertTriangle className="h-3.5 w-3.5" />
            )}
            SOS
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="h-8 bg-background/80 backdrop-blur-sm shadow-sm text-xs gap-1.5 px-3 rounded-full hover:bg-background"
            onClick={() => setShowParticipants(true)}
          >
            <Users className="h-3.5 w-3.5" />
            View Participants
          </Button>
        </div>
      )}

      {/* SOS Dialog */}
      <Dialog open={sosDialogOpen} onOpenChange={setSosDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-destructive flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Emergency SOS
            </DialogTitle>
            <DialogDescription>
              This will send your current location and an alert to event organizers immediately.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Add optional details (e.g., 'Medical emergency', 'Fire')..."
              value={sosMessage}
              onChange={(e) => setSosMessage(e.target.value)}
              className="resize-none"
            />
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setSosDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => handleSOS(sosMessage)}
              disabled={sendingSOS}
            >
              {sendingSOS ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Send Emergency Alert
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Status Bar */}
      {(error || !isJoined) && (
        <div
          className={`text-[10px] text-center py-1 ${isReadOnly
              ? "bg-muted text-muted-foreground"
              : error
                ? "bg-destructive/10 text-destructive"
                : "bg-muted/50 text-muted-foreground"
            }`}
        >
          {error || (
            <span className="flex items-center justify-center gap-1">
              <Loader2 className="h-2 w-2 animate-spin" /> Connecting...
            </span>
          )}
        </div>
      )}

      {/* Message Area */}
      <div
        className="flex-1 overflow-y-auto no-scrollbar"
        id="message-container"
      >
        <div className="min-h-full flex flex-col justify-end p-3">
          {messages.length === 0 && isJoined && !isReadOnly && (
            <div className="text-center text-xs text-muted-foreground mb-4 opacity-50">
              No messages yet. Say hello!
            </div>
          )}

          {messages.map((msg, idx) => {
            const isMe = msg.isSelf || msg.sender_id === currentUserId;
            return (
              <div
                key={idx}
                className={`flex mb-3 ${isMe ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm break-words shadow-sm ${
                    isMe
                      ? "bg-primary text-primary-foreground rounded-br-sm"
                      : "bg-muted text-foreground rounded-bl-sm"
                  }`}
                >
                  {!isMe && (
                    <div className="text-[11px] text-muted-foreground mb-1 font-medium leading-none">
                      {getSenderName(msg)}
                    </div>
                  )}
                  {msg.content}
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-3 bg-background border-t">
        <form onSubmit={handleSend} className="flex gap-2 items-center">
          <Input
            placeholder={
              isReadOnly
                ? "Chat is read-only"
                : isJoined
                  ? "Type a message..."
                  : "Connecting..."
            }
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={!isJoined || isReadOnly}
            className="h-10 text-sm rounded-full bg-muted/50 border-0 focus-visible:ring-1 focus-visible:ring-primary"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!inputValue.trim() || !isJoined || isReadOnly}
            className="rounded-full h-10 w-10 shrink-0"
          >
            <Send className="h-4 w-4 ml-0.5" />
          </Button>
        </form>
      </div>
    </div>
  );
}
