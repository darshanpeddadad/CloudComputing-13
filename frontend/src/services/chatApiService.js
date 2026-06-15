import axios from "axios";
import { baseUrl } from "../routes";
import { store } from "../store/store";

const getAuthHeaders = () => {
    const state = store.getState();
    const token = state.auth.user?.access_token;
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
};

const chatApiService = {
    fetchRooms: async () => {
        try {
            const response = await axios.get(`${baseUrl}chat/rooms`, {
                headers: getAuthHeaders(),
            });
            return response.data.data || [];
        } catch (error) {
            console.error("Failed to fetch chat rooms", error);
            return [];
        }
    },

    fetchHistory: async (roomId, limit = 50, before = null) => {
        try {
            const params = { limit };
            if (before) params.before = before;

            const response = await axios.get(`${baseUrl}chat/rooms/${roomId}/messages`, {
                headers: getAuthHeaders(),
                params,
            });
            return response.data.data || [];
        } catch (error) {
            console.error("Failed to fetch history", error);
            return [];
        }
    },

    markRead: async (roomId, messageId = null) => {
        try {
            await axios.post(
                `${baseUrl}chat/rooms/${roomId}/read`,
                { message_id: messageId },
                { headers: getAuthHeaders() }
            );
        } catch (error) {
            console.error("Failed to mark read", error);
        }
    },

    fetchAdmins: async () => {
        try {
            const response = await axios.get(`${baseUrl}admins/`, {
                headers: getAuthHeaders(),
            });
            return response.data.data?.admins || [];
        } catch (error) {
            console.error("Failed to fetch admins", error);
            return [];
        }
    },
};

export default chatApiService;
