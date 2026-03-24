import { create } from 'zustand';
import type { User, LoginCredentials, RegisterData } from '../types/auth';
import { getDefaultTrack } from '../types/auth';
import { apiClient } from '../services/apiClient';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  setAccessToken: (token: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: true, // starts true for initial auth check
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await apiClient.post('/api/v1/auth/login', credentials);
      set({
        user: data.data.user,
        accessToken: data.data.accessToken,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.error?.message || '로그인에 실패했습니다.',
        isLoading: false,
      });
      throw err;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const { data: res } = await apiClient.post('/api/v1/auth/signup', data);
      set({
        user: res.data.user,
        accessToken: res.data.accessToken,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.error?.message || '회원가입에 실패했습니다.',
        isLoading: false,
      });
      throw err;
    }
  },

  logout: async () => {
    try {
      await apiClient.post('/api/v1/auth/logout');
    } catch {
      // ignore logout errors
    } finally {
      get().clearAuth();
    }
  },

  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user, isAuthenticated: true }),
  clearAuth: () =>
    set({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    }),

  initializeAuth: async () => {
    try {
      // Silent refresh - try to restore session from HttpOnly cookie
      const { data } = await apiClient.post('/api/v1/auth/refresh');
      set({
        user: data.data.user,
        accessToken: data.data.accessToken,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },
}));
