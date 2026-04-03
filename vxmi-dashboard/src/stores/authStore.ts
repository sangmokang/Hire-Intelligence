import { create } from 'zustand';
import type { User, LoginCredentials, RegisterData } from '../types/auth';
import { apiClient } from '../services/apiClient';

const AUTH_STORAGE_KEY = 'vxmi-auth-session';

interface PersistedAuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
}

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

function getStorage(rememberMe = false): Storage | null {
  if (typeof window === 'undefined') return null;
  return rememberMe ? window.localStorage : window.sessionStorage;
}

function readPersistedAuth(): PersistedAuthState | null {
  if (typeof window === 'undefined') return null;

  for (const storage of [window.localStorage, window.sessionStorage]) {
    const raw = storage.getItem(AUTH_STORAGE_KEY);
    if (!raw) continue;

    try {
      return JSON.parse(raw) as PersistedAuthState;
    } catch {
      storage.removeItem(AUTH_STORAGE_KEY);
    }
  }

  return null;
}

function persistAuthState(state: PersistedAuthState, rememberMe = false): void {
  if (typeof window === 'undefined') return;

  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);

  const storage = getStorage(rememberMe);
  storage?.setItem(AUTH_STORAGE_KEY, JSON.stringify(state));
}

function clearPersistedAuth(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
}

// 로그인/회원가입 후 전체 프로필을 가져오는 헬퍼
async function fetchProfile(): Promise<User> {
  const { data } = await apiClient.get('/api/v1/auth/me');
  const profile = (data.data.user ?? data.data) as User;
  useAuthStore.getState().setUser(profile);
  return profile;
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
      const user = await fetchProfile();
      persistAuthState({
        accessToken: data.data.accessToken,
        refreshToken: data.data.refreshToken || null,
        user,
      }, credentials.rememberMe);
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
      const user = await fetchProfile();
      persistAuthState({
        accessToken: res.data.accessToken,
        refreshToken: res.data.refreshToken || null,
        user,
      });
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
    (() => {
      clearPersistedAuth();
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    })(),

  initializeAuth: async () => {
    try {
      const persisted = readPersistedAuth();
      const accessToken = get().accessToken || persisted?.accessToken || null;
      const refreshToken = get().refreshToken || persisted?.refreshToken || null;
      const persistedUser = get().user || persisted?.user || null;

      if (accessToken || refreshToken || persistedUser) {
        set({
          accessToken,
          refreshToken,
          user: persistedUser,
          isAuthenticated: Boolean(accessToken && persistedUser),
        });
      }

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
      const user = await fetchProfile();
      persistAuthState({
        accessToken: data.data.accessToken,
        refreshToken: data.data.refreshToken || get().refreshToken,
        user,
      }, Boolean(window.localStorage.getItem(AUTH_STORAGE_KEY)));
      set({ isAuthenticated: true, isLoading: false });
    } catch {
      get().clearAuth();
    }
  },
}));
