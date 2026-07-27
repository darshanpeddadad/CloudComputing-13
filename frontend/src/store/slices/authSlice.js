import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import axios from "axios";
import { baseUrl, routes } from "@/routes";
import authApiService from "../../services/authApiService";

const initialState = {
  isAppLoading: true,
  user: null,
  isRegistered: false,
  isAuthenticated: false,
  is2FARequired: false,
  tempToken: null,
  loading: false,
  error: null,
};

export const registerUser = createAsyncThunk(
  "auth/register",
  async (credentials, { rejectWithValue }) => {
    try {
      const res = await axios.post(baseUrl + routes.register, credentials);

      return res.data;
    } catch (error) {
      return rejectWithValue("Registration failed. Please try again.");
    }
  }
);

export const loginUser = createAsyncThunk(
  "auth/login",
  async (credentials, { rejectWithValue }) => {
    try {
      const res = await axios.post(baseUrl + routes.login, credentials);
      return res.data.data;
    } catch (error) {
      return rejectWithValue("Invalid credentials. Please try again.");
    }
  }
);

export const verify2FALogin = createAsyncThunk(
  "auth/verify2FALogin",
  async ({ tempToken, code }, { rejectWithValue }) => {
    try {
      const res = await authApiService.login2FA(tempToken, code);
      return res.data;
    } catch (error) {
      return rejectWithValue("Invalid 2FA code. Please try again.");
    }
  }
);

// Global auth state
const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    finishAppLoading: (state) => {
      state.isAppLoading = false;
    },
    autoLogin: (state, { payload }) => {
      state.isAppLoading = false;
      state.user = payload;
      state.isAuthenticated = true;
    },
    logout: (state) => {
      state.user = null;
      localStorage.removeItem("user");
      state.isAuthenticated = false;
      state.isRegistered = false;
      state.is2FARequired = false;
      state.tempToken = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetRegistration: (state) => {
      state.isRegistered = false;
    },
    reset2FAState: (state) => {
      state.is2FARequired = false;
      state.tempToken = null;
    },
  },
  extraReducers: (builder) => {
    // Registration
    builder
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.loading = false;
        state.isRegistered = true;
        state.error = null;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });

    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload.two_factor_required) {
          state.is2FARequired = true;
          state.tempToken = action.payload.temp_token;
          state.isAuthenticated = false;
        } else {
          state.user = action.payload;
          localStorage.setItem("user", JSON.stringify(action.payload));
          state.isAuthenticated = true;
          state.is2FARequired = false;
          state.tempToken = null;
        }
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });

    // 2FA Verification
    builder
      .addCase(verify2FALogin.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verify2FALogin.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        localStorage.setItem("user", JSON.stringify(action.payload));
        state.isAuthenticated = true;
        state.is2FARequired = false;
        state.tempToken = null;
        state.error = null;
      })
      .addCase(verify2FALogin.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { finishAppLoading, autoLogin, logout, clearError, resetRegistration, reset2FAState } =
  authSlice.actions;
export default authSlice.reducer;
