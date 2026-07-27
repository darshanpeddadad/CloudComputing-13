import { useState, useEffect } from "react";
import { useSelector } from "react-redux";
import { MessageSquare, X, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

import socketService from "@/services/socketService";
import chatApiService from "@/services/chatApiService";

import RoomList from "./RoomList";
import ChatRoomView from "./ChatRoomView";

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);

  const [rooms, setRooms] = useState([]);
  const [activeRoom, setActiveRoom] = useState(null);

  // Authentication check
  const authState = useSelector((state) => state.auth || {});
  const isAuthenticated = authState.isAuthenticated;
  const user = authState.user;
  const token = user?.access_token;
  const currentUserId = user?.user?.id;

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setRooms([]);
      setActiveRoom(null);
    }
  }, [isAuthenticated, token]);

  // Load Rooms
  useEffect(() => {
    if (isOpen && isAuthenticated && !activeRoom) {
      chatApiService.fetchRooms().then(setRooms).catch(console.error);
    }
  }, [isOpen, isAuthenticated, activeRoom]);

  // Handle External Direct Join (e.g. from Event Details)
  useEffect(() => {
    const unsub = socketService.onDirectJoined(async (data) => {
      setIsOpen(true);
      const freshRooms = await chatApiService.fetchRooms();
      setRooms(freshRooms || []);

      const targetId = data.chat_room_id || data.room_id;
      const found = freshRooms?.find((r) => r.id === targetId);
      if (found) setActiveRoom(found);
    });
    return () => unsub();
  }, []);

  const getRoomTitle = (room) => {
    if (!room) return "Chat";
    if (room.room_type === "event_group" || room.type === "event_group") {
      return room.title || "Event Group";
    }

    // Direct Chat Title
    if (room.other_user?.name && room.other_user.id !== currentUserId)
      return room.other_user.name;
    const other = room.participants?.find((p) => p.user_id !== currentUserId);
    return other?.name || room.title || "Direct Chat";
  };

  if (!isAuthenticated) return null;

  if (!isOpen) {
    return (
      <Button
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50 animate-in zoom-in duration-300"
        onClick={() => setIsOpen(true)}
      >
        <MessageSquare className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <div className="fixed right-6 bottom-6 w-[380px] bg-background border shadow-2xl rounded-2xl flex flex-col z-50 transition-all duration-300 h-[600px]">
      {/* Header */}
      <div className="p-4 border-b flex justify-between items-center bg-primary/5 rounded-t-2xl">
        <div className="flex items-center gap-2">
          {activeRoom ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 mr-1"
                onClick={(e) => {
                  setActiveRoom(null);
                }}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <span className="font-semibold text-sm truncate max-w-[200px]">
                {getRoomTitle(activeRoom)}
              </span>
            </>
          ) : (
            <span className="font-semibold text-sm">Messages</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => {
              setIsOpen(false);
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col bg-background rounded-b-2xl">
        {activeRoom ? (
          <ChatRoomView activeRoom={activeRoom} />
        ) : (
          <RoomList
            rooms={rooms}
            onSelect={setActiveRoom}
            currentUserId={currentUserId}
          />
        )}
      </div>
    </div>
  );
}
