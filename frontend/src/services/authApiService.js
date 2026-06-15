import axios from "axios";
import { baseUrl } from "../routes";
import { store } from "../store/store";

const getAuthHeaders = () => {
    const state = store.getState();
    const token = state.auth.user?.access_token;
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
};

const authApiService = {
    // Standard login
    login: async (credentials) => {
        try {
            const response = await axios.post(`${baseUrl}auth/login`, credentials);
            return response.data;
        } catch (error) {
            console.error("Login failed", error);
            throw error;
        }
    },

    // Init 2FA setup
    enable2FA: async () => {
        try {
            const response = await axios.post(`${baseUrl}auth/2fa/enable`, {}, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to enable 2FA", error);
            throw error;
        }
    },

    // Verify TOTP to enable
    verify2FA: async (code) => {
        try {
            const response = await axios.post(`${baseUrl}auth/2fa/verify`, { code }, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to verify 2FA", error);
            throw error;
        }
    },

    // Login with 2FA
    login2FA: async (tempToken, code) => {
        try {
            const response = await axios.post(`${baseUrl}auth/2fa/login`, {
                temp_token: tempToken,
                code: code
            });
            return response.data;
        } catch (error) {
            console.error("2FA Login failed", error);
            throw error;
        }
    },

    // Disable 2FA
    disable2FA: async () => {
        try {
            const response = await axios.post(`${baseUrl}auth/2fa/disable`, {}, {
                headers: getAuthHeaders(),
            });
            return response.data;
        } catch (error) {
            console.error("Failed to disable 2FA", error);
            throw error;
        }
    }
};

export default authApiService;
