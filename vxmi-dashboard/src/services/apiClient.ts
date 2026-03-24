import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Request: inject Access Token from Zustand memory
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response: handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Try Supabase client-side refresh first
        const { supabase } = await import('../lib/supabase');
        const { data: refreshData } = await supabase.auth.refreshSession();

        if (refreshData.session) {
          const newToken = refreshData.session.access_token;
          useAuthStore.getState().setAccessToken(newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }

        // If Supabase refresh fails, clear auth
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      } catch {
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);
