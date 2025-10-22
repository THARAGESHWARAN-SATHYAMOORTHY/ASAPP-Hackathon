import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Customer API
export const customerAPI = {
  sendQuery: async (query, sessionId = null) => {
    const response = await api.post('/customer/query', {
      query,
      session_id: sessionId,
    });
    return response.data;
  },

  sendInput: async (sessionId, inputValue) => {
    const response = await api.post('/customer/input', {
      session_id: sessionId,
      input_value: inputValue,
    });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/customer/session/${sessionId}`);
    return response.data;
  },
};

// Admin API
export const adminAPI = {
  getRequestTypes: async () => {
    const response = await api.get('/admin/request-types');
    return response.data;
  },

  getRequestType: async (id) => {
    const response = await api.get(`/admin/request-types/${id}`);
    return response.data;
  },

  createRequestType: async (data) => {
    const response = await api.post('/admin/request-types', data);
    return response.data;
  },

  updateRequestType: async (id, data) => {
    const response = await api.put(`/admin/request-types/${id}`, data);
    return response.data;
  },

  deleteRequestType: async (id) => {
    const response = await api.delete(`/admin/request-types/${id}`);
    return response.data;
  },

  getPolicies: async (policyType = null) => {
    const params = policyType ? { policy_type: policyType } : {};
    const response = await api.get('/admin/policies', { params });
    return response.data;
  },

  createPolicy: async (data) => {
    const response = await api.post('/admin/policies', null, { params: data });
    return response.data;
  },

  initializePolicies: async () => {
    const response = await api.post('/admin/policies/initialize');
    return response.data;
  },
};

// Airline API (for testing)
export const airlineAPI = {
  getBooking: async (pnr) => {
    const response = await api.get(`/flight/booking?pnr=${pnr}`);
    return response.data;
  },

  cancelFlight: async (data) => {
    const response = await api.post('/flight/cancel', data);
    return response.data;
  },

  getAvailableSeats: async (data) => {
    const response = await api.post('/flight/available_seats', data);
    return response.data;
  },

  getFlightStatus: async (pnr) => {
    const response = await api.get(`/flight/status?pnr=${pnr}`);
    return response.data;
  },
};

export default api;

