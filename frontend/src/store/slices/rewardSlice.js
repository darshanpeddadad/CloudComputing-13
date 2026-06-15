import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import rewardApiService from "@/services/rewardApiService";

const initialState = {
  // Profile data
  profile: null,
  profileLoading: false,
  profileError: null,

  // Transaction history
  transactions: [],
  transactionsTotal: 0,
  transactionsPage: 1,
  transactionsLoading: false,
  transactionsError: null,

  // Leaderboard
  leaderboard: [],
  leaderboardTotal: 0,
  leaderboardPeriod: "all_time",
  leaderboardPage: 1,
  leaderboardLoading: false,
  leaderboardError: null,
  myRank: null,

  // Badges
  badges: [],
  badgesLoading: false,
  badgesError: null,

  // Redemption
  redemptionPreview: null,
  redemptionLoading: false,
  redemptionError: null,
  redemptionRate: null,

  // Streak - group all streak related states into a nested object for better organization
  streak: {
    data: null,
    loading: false,
    error: null,
    multipliers: [],
  },
};

// Async thunks
export const fetchMyProfile = createAsyncThunk(
  "rewards/fetchMyProfile",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getMyProfile();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch profile",
      );
    }
  },
);

export const fetchTransactions = createAsyncThunk(
  "rewards/fetchTransactions",
  async ({ page = 1, pageSize = 20 }, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getMyTransactions(page, pageSize);
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch transactions",
      );
    }
  },
);

export const fetchLeaderboard = createAsyncThunk(
  "rewards/fetchLeaderboard",
  async (
    { period = "all_time", page = 1, pageSize = 50 },
    { rejectWithValue },
  ) => {
    try {
      const response = await rewardApiService.getLeaderboard(
        period,
        page,
        pageSize,
      );
      return { ...response, period };
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch leaderboard",
      );
    }
  },
);

export const fetchMyRank = createAsyncThunk(
  "rewards/fetchMyRank",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getMyRank();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch rank",
      );
    }
  },
);

export const fetchAllBadges = createAsyncThunk(
  "rewards/fetchAllBadges",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getAllBadges();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch badges",
      );
    }
  },
);

export const previewRedemption = createAsyncThunk(
  "rewards/previewRedemption",
  async ({ pointsToRedeem, eventId }, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.previewRedemption(
        pointsToRedeem,
        eventId,
      );
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to preview redemption",
      );
    }
  },
);

export const redeemPoints = createAsyncThunk(
  "rewards/redeemPoints",
  async (
    { pointsToRedeem, redemptionType = "discount", eventId },
    { rejectWithValue },
  ) => {
    try {
      const response = await rewardApiService.redeemPoints(
        pointsToRedeem,
        redemptionType,
        eventId,
      );
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to redeem points",
      );
    }
  },
);

export const fetchRedemptionRate = createAsyncThunk(
  "rewards/fetchRedemptionRate",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getRedemptionRate();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch redemption rate",
      );
    }
  },
);

export const fetchMyStreak = createAsyncThunk(
  "rewards/fetchMyStreak",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getMyStreak();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch streak info",
      );
    }
  },
);

export const fetchStreakMultipliers = createAsyncThunk(
  "rewards/fetchStreakMultipliers",
  async (_, { rejectWithValue }) => {
    try {
      const response = await rewardApiService.getStreakMultipliers();
      return response;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || "Failed to fetch streak multipliers",
      );
    }
  },
);

const rewardSlice = createSlice({
  name: "rewards",
  initialState,
  reducers: {
    clearRedemptionPreview: (state) => {
      state.redemptionPreview = null;
      state.redemptionError = null;
    },
    clearErrors: (state) => {
      state.profileError = null;
      state.transactionsError = null;
      state.leaderboardError = null;
      state.badgesError = null;
      state.redemptionError = null;
    },
    setLeaderboardPeriod: (state, action) => {
      state.leaderboardPeriod = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Profile
      .addCase(fetchMyProfile.pending, (state) => {
        state.profileLoading = true;
        state.profileError = null;
      })
      .addCase(fetchMyProfile.fulfilled, (state, action) => {
        state.profileLoading = false;
        state.profile = action.payload;
      })
      .addCase(fetchMyProfile.rejected, (state, action) => {
        state.profileLoading = false;
        state.profileError = action.payload;
      })

      // Transactions
      .addCase(fetchTransactions.pending, (state) => {
        state.transactionsLoading = true;
        state.transactionsError = null;
      })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.transactionsLoading = false;
        state.transactions = action.payload.transactions;
        state.transactionsTotal = action.payload.total;
        state.transactionsPage = action.payload.page;
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.transactionsLoading = false;
        state.transactionsError = action.payload;
      })

      // Leaderboard
      .addCase(fetchLeaderboard.pending, (state) => {
        state.leaderboardLoading = true;
        state.leaderboardError = null;
      })
      .addCase(fetchLeaderboard.fulfilled, (state, action) => {
        state.leaderboardLoading = false;
        state.leaderboardError = null;
        // Handle case where server returns null/undefined data
        if (action.payload && action.payload.entries) {
          state.leaderboard = action.payload.entries;
          state.leaderboardTotal = action.payload.total_users || 0;
          state.leaderboardPage = action.payload.page || 1;
          state.leaderboardPeriod = action.payload.period || "all_time";
        } else {
          // Fallback for malformed response
          state.leaderboard = [];
          state.leaderboardTotal = 0;
          state.leaderboardPage = 1;
          state.leaderboardError = "Server returned invalid data";
        }
      })
      .addCase(fetchLeaderboard.rejected, (state, action) => {
        state.leaderboardLoading = false;
        state.leaderboardError = action.payload;
      })

      // My Rank
      .addCase(fetchMyRank.fulfilled, (state, action) => {
        state.myRank = action.payload;
      })

      // Badges
      .addCase(fetchAllBadges.pending, (state) => {
        state.badgesLoading = true;
        state.badgesError = null;
      })
      .addCase(fetchAllBadges.fulfilled, (state, action) => {
        state.badgesLoading = false;
        state.badges = action.payload.badges;
      })
      .addCase(fetchAllBadges.rejected, (state, action) => {
        state.badgesLoading = false;
        state.badgesError = action.payload;
      })

      // Redemption Preview
      .addCase(previewRedemption.pending, (state) => {
        state.redemptionLoading = true;
        state.redemptionError = null;
      })
      .addCase(previewRedemption.fulfilled, (state, action) => {
        state.redemptionLoading = false;
        state.redemptionPreview = action.payload;
      })
      .addCase(previewRedemption.rejected, (state, action) => {
        state.redemptionLoading = false;
        state.redemptionError = action.payload;
      })

      // Redeem Points
      .addCase(redeemPoints.pending, (state) => {
        state.redemptionLoading = true;
        state.redemptionError = null;
      })
      .addCase(redeemPoints.fulfilled, (state, action) => {
        state.redemptionLoading = false;
        state.redemptionPreview = null;
        // Update profile balance
        if (state.profile) {
          state.profile.current_points = action.payload.new_balance;
        }
      })
      .addCase(redeemPoints.rejected, (state, action) => {
        state.redemptionLoading = false;
        state.redemptionError = action.payload;
      })

      // Redemption Rate
      .addCase(fetchRedemptionRate.fulfilled, (state, action) => {
        state.redemptionRate = action.payload;
      })

      // Streak
      .addCase(fetchMyStreak.pending, (state) => {
        state.streak.loading = true;
        state.streak.error = null;
      })
      .addCase(fetchMyStreak.fulfilled, (state, action) => {
        state.streak.loading = false;
        state.streak.data = action.payload;
      })
      .addCase(fetchMyStreak.rejected, (state, action) => {
        state.streak.loading = false;
        state.streak.error = action.payload;
      })

      // Streak Multipliers
      .addCase(fetchStreakMultipliers.fulfilled, (state, action) => {
        state.streak.multipliers = action.payload.multipliers || [];
      });
  },
});

export const {
  clearRedemptionPreview,
  clearErrors,
  setLeaderboardPeriod,
} = rewardSlice.actions;

export default rewardSlice.reducer;