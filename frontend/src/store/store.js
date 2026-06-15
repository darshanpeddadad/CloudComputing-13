import { configureStore } from "@reduxjs/toolkit";
import authReducer from "./slices/authSlice";
import themeReducer from "./slices/themeSlice";
import rewardReducer from "./slices/rewardSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    theme: themeReducer,
    rewards: rewardReducer,
  },
});
