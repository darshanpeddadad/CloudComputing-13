import axios from "axios";
import { baseUrl } from "../routes";
import { store } from "../store/store";

const getAuthHeaders = () => {
    const state = store.getState();
    const token = state.auth.user?.access_token;
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
};

const userApiService = {
    fetchUserDetails: async (userId) => {
        try {
            const response = await axios.get(`${baseUrl}users/${userId}/details`, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to fetch user details", error);
            throw error;
        }
    },

    saveUserDetails: async (userId, details) => {
        try {
            const response = await axios.patch(`${baseUrl}users/${userId}/details`, details, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to save user details", error);
            throw error;
        }
    },

    changePassword: async (userId, passwordData) => {
        try {
            const response = await axios.patch(`${baseUrl}users/${userId}/details/password`, passwordData, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to change password", error);
            throw error;
        }
    },

    getBookmarks: async (userId) => {
        try {
            const response = await axios.get(`${baseUrl}users/${userId}/bookmarks`, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to fetch bookmarks", error);
            throw error;
        }
    },

    addBookmark: async (userId, eventId) => {
        try {
            const response = await axios.post(`${baseUrl}users/${userId}/bookmarks/${eventId}`, {}, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to add bookmark", error);
            throw error;
        }
    },

    removeBookmark: async (userId, eventId) => {
        try {
            const response = await axios.delete(`${baseUrl}users/${userId}/bookmarks/${eventId}`, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to remove bookmark", error);
            throw error;
        }
    },

    checkBookmarkStatus: async (userId, eventId) => {
        try {
            const response = await axios.get(`${baseUrl}users/${userId}/bookmarks/${eventId}`, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to check bookmark status", error);
            throw error;
        }
    },
};

export default userApiService;
