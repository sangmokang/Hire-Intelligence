import { create } from 'zustand';
import type { User, LoginCredentials, RegisterData } from '../types/auth';
import { apiClient } from '../services/apiClient';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
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

// 로그인/회원가입 후 전체 프로필을 가져오는 헬퍼
async function fetchProfile(): Promise<void> {
  const { data } = await apiClient.get('/api/v1/auth/me');
  const profile = data.data;
  useAuthStore.getState().setUser(profile);
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (credentials) => {
    set({ error: null });
    try {
      const { data } = await apiClient.post('/api/v1/auth/login', credentials);
      // 토큰 먼저 저장 (fetchProfile 요청에 Authorization 헤더 필요)
      set({
        accessToken: data.data.accessToken,
        refreshToken: data.data.refreshToken || null,
      });
      // /auth/me에서 전체 프로필 가져오기
      await fetchProfile();
      set({ isAuthenticated: true });
    } catch (err: unknown) {
      // AxiosError 응답에서 서버 메시지를 우선 추출
      const axiosData = (err as { response?: { data?: { detail?: string; error?: { message?: string } } } })?.response?.data;
      const message = axiosData?.error?.message || axiosData?.detail
        || (err instanceof Error ? err.message : '로그인에 실패했습니다.');
      set({ error: message });
      throw err;
    }
  },

  register: async (data) => {
    set({ error: null });
    try {
      const { data: res } = await apiClient.post('/api/v1/auth/signup', data);
      // 토큰 먼저 저장
      set({
        accessToken: res.data.accessToken,
        refreshToken: res.data.refreshToken || null,
      });
      // /auth/me에서 전체 프로필 가져오기
      await fetchProfile();
      set({ isAuthenticated: true });
    } catch (err: unknown) {
      const axiosData = (err as { response?: { data?: { detail?: string; error?: { message?: string } } } })?.response?.data;
      const message = axiosData?.error?.message || axiosData?.detail
        || (err instanceof Error ? err.message : '회원가입에 실패했습니다.');
      set({ error: message });
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
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    }),

  initializeAuth: async () => {
    try {
      const refreshToken = get().refreshToken;
      if (!refreshToken) {
        set({ isLoading: false });
        return;
      }
      // refreshToken을 POST body에 포함하여 세션 복원
      const { data } = await apiClient.post('/api/v1/auth/refresh', { refreshToken });
      set({
        accessToken: data.data.accessToken,
        refreshToken: data.data.refreshToken || get().refreshToken,
      });
      await fetchProfile();
      set({ isAuthenticated: true, isLoading: false });
    } catch {
      get().clearAuth();
    }
  },
}));
