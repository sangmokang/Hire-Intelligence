import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/authService';
import { useAuthStore } from '../stores/authStore';
import { supabase } from '../lib/supabase';

// Query key factory
export const authKeys = {
  session: ['auth', 'session'] as const,
};

// Get current session query
export function useSession() {
  return useQuery({
    queryKey: authKeys.session,
    queryFn: () => authService.getSession(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  });
}

// Listen to Supabase auth state changes and sync with Zustand store
export function useAuthStateSync() {
  const { setUser, clearAuth } = useAuthStore();
  const queryClient = useQueryClient();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        // Invalidate session cache
        queryClient.invalidateQueries({ queryKey: authKeys.session });
      } else if (event === 'SIGNED_OUT') {
        clearAuth();
        queryClient.clear();
      } else if (event === 'TOKEN_REFRESHED' && session) {
        queryClient.invalidateQueries({ queryKey: authKeys.session });
      }
    });

    return () => subscription.unsubscribe();
  }, [setUser, clearAuth, queryClient]);
}

// Sign in mutation
export function useSignIn() {
  const queryClient = useQueryClient();
  const { login: _login } = useAuthStore();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.signIn(email, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.session });
    },
    onError: (error: Error) => {
      console.error('로그인 오류:', error.message);
    },
  });
}

// Sign up mutation
export function useSignUp() {
  return useMutation({
    mutationFn: ({
      email,
      password,
      metadata,
    }: {
      email: string;
      password: string;
      metadata: { name: string; category: string };
    }) => authService.signUp(email, password, metadata),
    onError: (error: Error) => {
      console.error('회원가입 오류:', error.message);
    },
  });
}

// Sign out mutation
export function useSignOut() {
  const queryClient = useQueryClient();
  const { clearAuth } = useAuthStore();

  return useMutation({
    mutationFn: () => authService.signOut(),
    onSuccess: () => {
      clearAuth();
      queryClient.clear();
    },
    onError: (error: Error) => {
      console.error('로그아웃 오류:', error.message);
    },
  });
}

// Google OAuth mutation
export function useSignInWithGoogle() {
  return useMutation({
    mutationFn: () => authService.signInWithGoogle(),
    onError: (error: Error) => {
      console.error('Google 로그인 오류:', error.message);
    },
  });
}

// Reset password mutation
export function useResetPassword() {
  return useMutation({
    mutationFn: (email: string) => authService.resetPassword(email),
    onError: (error: Error) => {
      console.error('비밀번호 재설정 오류:', error.message);
    },
  });
}
