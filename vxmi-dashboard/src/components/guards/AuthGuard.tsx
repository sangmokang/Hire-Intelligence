import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { supabase } from '../../lib/supabase';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading, setUser, clearAuth } = useAuthStore();
  const location = useLocation();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // Check Supabase session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session && !isAuthenticated) {
        clearAuth();
      }
      setChecking(false);
    });

    // Listen to auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        clearAuth();
      }
    });

    return () => subscription.unsubscribe();
  }, [isAuthenticated, setUser, clearAuth]);

  if (isLoading || checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
