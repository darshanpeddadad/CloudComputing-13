export const baseUrl = import.meta.env.VITE_BASE_HTTP_URL || "http://localhost:8000/api/";

export const routes = {
  register: "auth/register",
  login: "auth/login",
  events: "events",
  chatRooms: "chat/rooms",
};
