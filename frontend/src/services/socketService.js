import { io } from "socket.io-client";
import { baseUrl } from "../routes";

const getSocketUrl = () => {
  try {
    const url = new URL(baseUrl);
    return url.origin;
  } catch (e) {
    return window.location.origin;
  }
};

class SocketService {
  constructor() {
    this.socket = null;
    this.token = null;
    // needed to queue joins and event listeners called before socket connect
    this.activeListeners = [];
    this.pendingRoomJoins = new Set();
  }

  // Socket Connection
  connect(token) {
    if (this.socket && this.socket.connected && this.token === token) return;
    if (this.socket) this.disconnect();

    this.token = token;
    const url = getSocketUrl();

    this.socket = io(url, {
      path: "/socket.io",
      transports: ["websocket"],
      auth: { token },
      reconnectionAttempts: 5,
    });

    this.socket.on("connect_error", (e) => console.error("[Socket] Error:", e));

    // process pending joins on connection (mostly for admin_global room)
    this.socket.on("connect", () => {
      this.pendingRoomJoins.forEach((room) => {
        this.socket.emit("join_room", { room });
      });
    });

    // re-attach listeners
    if (this.activeListeners.length > 0) {
      this.activeListeners.forEach(({ event, handler }) => {
        this.socket.on(event, handler);
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.token = null;
    }
  }

  // helper to queue listeners if socket still not connected
  subscribe(event, handler) {
    this.activeListeners.push({ event, handler });
    if (this.socket) {
      this.socket.on(event, handler);
    }
    return () => {
      this.activeListeners = this.activeListeners.filter(
        (l) => l.handler !== handler || l.event !== event
      );
      if (this.socket) {
        this.socket.off(event, handler);
      }
    };
  }

  // helper to get event id which is available in different fields for group and direct chats
  getEventId(room) {
    if (!room) return null;
    if (room.event_id) return room.event_id;
    if (room.context?.startsWith("event:")) return room.context.split(":")[1];
    return null;
  }

  joinRoom(room, currentUserId) {
    if (!this.socket) return;

    if (room.room_type === "direct") {
      const eventId = this.getEventId(room);
      const targetUserId =
        room.other_user?.id ||
        room.participants?.find((p) => p.user_id !== currentUserId)?.user_id;

      if (targetUserId) {
        this.socket.emit("direct:join", {
          target_user_id: targetUserId,
          event_id: eventId,
        });
      }
    } else {
      this.socket.emit("event_group:join", { event_id: room.event_id });
    }
  }

  leaveRoom(room) {
    if (!this.socket) return;
    if (room.room_type === "direct") return;

    const eventId = this.getEventId(room);
    if (eventId) {
      this.socket.emit("event_group:leave", {
        room_id: `event:group:${eventId}`,
        event_id: eventId,
      });
    }
  }

  sendMessage(room, content, socketRoomId) {
    if (!this.socket) return;

    if (room.room_type === "direct") {
      this.socket.emit("direct:message", {
        room_id: socketRoomId || room.id,
        content,
      });
    } else {
      this.socket.emit("event_group:message", { room_id: room.id, content });
    }
  }

  // added to manually join the admin_global room
  joinAdminRoom() {
    const room = "admin_global";
    if (!this.pendingRoomJoins.has(room)) {
      this.pendingRoomJoins.add(room);
      if (this.socket && this.socket.connected) {
        this.socket.emit("join_room", { room });
      }
    }
  }

  joinDirect(targetId, eventId) {
    if (!this.socket) return;
    this.socket.emit("direct:join", {
      target_user_id: targetId,
      event_id: eventId,
    });
  }

  // Listeners
  onAnyJoin(cb) {
    const handler = (data) => cb(data);
    const unsub1 = this.subscribe("event_group:joined", handler);
    const unsub2 = this.subscribe("direct:joined", handler);
    return () => {
      unsub1();
      unsub2();
    };
  }

  onAnyMessage(cb) {
    const handler = (data) => cb(data);
    const unsub1 = this.subscribe("event_group:message", handler);
    const unsub2 = this.subscribe("direct:message", handler);
    return () => {
      unsub1();
      unsub2();
    };
  }

  onAnyError(cb) {
    const handler = (data) => cb(data);
    const unsub1 = this.subscribe("event_group:error", handler);
    const unsub2 = this.subscribe("direct:error", handler);
    return () => {
      unsub1();
      unsub2();
    };
  }

  onDirectJoined(cb) {
    return this.subscribe("direct:joined", (data) => cb(data));
  }

  onParticipantsList(cb) {
    return this.subscribe("event_group:participants", (data) => cb(data));
  }

  onSOSAlert(cb) {
    return this.subscribe("sos:alert", (data) => cb(data));
  }
}

const socketService = new SocketService();
export default socketService;
