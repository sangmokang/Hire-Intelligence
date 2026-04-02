import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { UserCategory } from '../types/auth';

// 카테고리별 대시보드 진입점 매핑 (PRD v3.0 section 3-A)
const CATEGORY_DEFAULT_ROUTE: Record<UserCategory, string> = {
  INHOUSE_HR: '/dashboard/top-companies',
  HEADHUNTER: '/dashboard/timeline',
  CHRO: '/dashboard/sd-matrix',
  JOB_SEEKER: '/dashboard/market-signals',
};

// SUPER_ADMIN 기본 진입점
const SUPER_ADMIN_DEFAULT_ROUTE = '/dashboard/top-companies';

// 인증되지 않은 경우 기본 진입점
const FALLBACK_ROUTE = '/dashboard/top-companies';

export function DashboardRedirect() {
  const user = useAuthStore((state) => state.user);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // SUPER_ADMIN 역할은 카테고리 무관하게 별도 진입점으로 이동
  if (user.role === 'SUPER_ADMIN') {
    return <Navigate to={SUPER_ADMIN_DEFAULT_ROUTE} replace />;
  }

  const targetRoute = CATEGORY_DEFAULT_ROUTE[user.category] ?? FALLBACK_ROUTE;
  return <Navigate to={targetRoute} replace />;
}
