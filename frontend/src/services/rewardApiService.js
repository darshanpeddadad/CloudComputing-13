import axios from "axios";
import { baseUrl } from "../routes";
import { store } from "../store/store";

const getAuthHeaders = () => {
  const state = store.getState();
  const user = state.auth.user;
  const token = user?.access_token || user?.user?.access_token;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
};

const rewardApiService = {
  /**
   * Get current user's reward profile
   */
  getMyProfile: async () => {
    const response = await axios.get(`${baseUrl}rewards/profile`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Get a specific user's reward profile
   */
  getUserProfile: async (userId) => {
    const response = await axios.get(`${baseUrl}rewards/profile/${userId}`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Get current user's point transaction history
   */
  getMyTransactions: async (page = 1, pageSize = 20) => {
    const response = await axios.get(`${baseUrl}rewards/transactions`, {
      headers: getAuthHeaders(),
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  /**
   * Get leaderboard
   * @param {string} period - 'all_time', 'weekly', or 'monthly'
   */
  getLeaderboard: async (period = "all_time", page = 1, pageSize = 50) => {
    try {
      const response = await axios.get(`${baseUrl}rewards/leaderboard`, {
        headers: getAuthHeaders(),
        params: { period, page, page_size: pageSize },
      });
      
      // Validate response structure
      if (!response.data) {
        throw new Error("No data received from server");
      }
      
      // Ensure entries is always an array
      const data = {
        ...response.data,
        entries: Array.isArray(response.data.entries) ? response.data.entries : [],
        total_users: response.data.total_users || 0,
        page: response.data.page || page,
      };
      
      return data;
    } catch (error) {
      // Re-throw with more specific error message
      if (error.response?.status === 404) {
        throw new Error("Leaderboard not found");
      } else if (error.response?.status >= 500) {
        throw new Error("Server error - please try again later");
      } else if (!navigator.onLine) {
        throw new Error("No internet connection");
      }
      throw error;
    }
  },

  /**
   * Get current user's rank on the leaderboard
   */
  getMyRank: async () => {
    const response = await axios.get(`${baseUrl}rewards/leaderboard/my-rank`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Preview a point redemption without committing
   */
  previewRedemption: async (pointsToRedeem, eventId = null) => {
    const response = await axios.post(
      `${baseUrl}rewards/redemption/preview`,
      {
        points_to_redeem: pointsToRedeem,
        event_id: eventId,
      },
      {
        headers: getAuthHeaders(),
      },
    );
    return response.data;
  },

  /**
   * Redeem points for a discount
   */
  redeemPoints: async (
    pointsToRedeem,
    redemptionType = "discount",
    eventId = null,
  ) => {
    const response = await axios.post(
      `${baseUrl}rewards/redeem`,
      {
        points_to_redeem: pointsToRedeem,
        redemption_type: redemptionType,
        event_id: eventId,
      },
      {
        headers: getAuthHeaders(),
      },
    );
    return response.data;
  },

  /**
   * Get current redemption rate
   */
  getRedemptionRate: async () => {
    const response = await axios.get(`${baseUrl}rewards/redemption/rate`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Get all available badges
   */
  getAllBadges: async () => {
    const response = await axios.get(`${baseUrl}rewards/badges`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Get current user's streak information
   */
  getMyStreak: async () => {
    try {
      const response = await axios.get(`${baseUrl}rewards/streak`, {
        headers: getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching user streak:", error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        "Failed to fetch streak information"
      );
    }
  },

  /**
   * Get all streak multiplier tiers
   */
  getStreakMultipliers: async () => {
    try {
      const response = await axios.get(`${baseUrl}rewards/streak/multipliers`, {
        headers: getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching streak multipliers:", error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        "Failed to fetch streak multipliers"
      );
    }
  },
};

export default rewardApiService;