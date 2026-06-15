import axios from "axios";
import { baseUrl } from "../routes";
import { store } from "../store/store";

const getHeaders = () => {
  const state = store.getState();
  const token = state.auth.user?.access_token || state.auth.token;
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
};

const sosApiService = {
  triggerSOS: async (data) => {
    const response = await axios.post(`${baseUrl}sos/`, data, { headers: getHeaders() });
    return response.data;
  },

  getEventAlerts: async (eventId) => {
    const response = await axios.get(`${baseUrl}sos/event/${eventId}`, { headers: getHeaders() });
    return response.data;
  },

  updateAlertStatus: async (alertId, status) => {
    const response = await axios.patch(
      `${baseUrl}sos/${alertId}`,
      { status },
      { headers: getHeaders() }
    );
    return response.data;
  },
};

export default sosApiService;
