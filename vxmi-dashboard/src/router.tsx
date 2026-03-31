import { createBrowserRouter, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';

// Layouts
import { AuthLayout } from './components/layout/AuthLayout';
import { DashboardLayout } from './components/layout/DashboardLayout';

// Guards
import { AuthGuard } from './components/guards/AuthGuard';
import { GuestGuard } from './components/guards/GuestGuard';
import { RoleGuard } from './components/guards/RoleGuard';
import { PlanGuard } from './components/guards/PlanGuard';

// Auth pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';

// Analysis views (existing)
import { TopCompaniesView } from './components/views/TopCompaniesView';
import { SDMatrixView } from './components/views/SDMatrixView';
import { CompanyTimelineView } from './components/views/CompanyTimelineView';
import { HiringTrendsView } from './components/views/HiringTrendsView';
import { ResumeMatchView } from './components/views/ResumeMatchView';
import { CompanyAnalysisView } from './components/views/CompanyAnalysisView';
import { JdInsightsView } from './components/views/JdInsightsView'
import { CompanyDnaView } from './components/views/CompanyDnaView';
import { CompanyCompareView } from './components/views/CompanyCompareView';

// My pages
import ProfilePage from './pages/my/ProfilePage';
import BillingPage from './pages/my/BillingPage';
import PlansPage from './pages/my/PlansPage';
import SettingsPage from './pages/my/SettingsPage';

// Placeholder components for future pages
// eslint-disable-next-line react-refresh/only-export-components
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
        <p className="text-gray-500">이 페이지는 준비 중입니다.</p>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  // Public / Guest routes
  {
    element: (
      <GuestGuard>
        <AuthLayout />
      </GuestGuard>
    ),
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
    ],
  },

  // Authenticated routes with DashboardLayout
  {
    element: (
      <AuthGuard>
        <DashboardLayout />
      </AuthGuard>
    ),
    children: [
      // Dashboard - redirect to default view
      { path: '/dashboard', element: <Navigate to="/dashboard/top-companies" replace /> },

      // Analysis views (existing 6 views)
      { path: '/dashboard/top-companies', element: <TopCompaniesView /> },
      { path: '/dashboard/sd-matrix', element: <SDMatrixView /> },
      { path: '/dashboard/timeline', element: (
        <PlanGuard requiredPlan="PRO">
          <CompanyTimelineView />
        </PlanGuard>
      ) },
      { path: '/dashboard/trends', element: (
        <PlanGuard requiredPlan="PRO">
          <HiringTrendsView />
        </PlanGuard>
      ) },
      { path: '/dashboard/resume-match', element: (
        <PlanGuard requiredPlan="PRO">
          <ResumeMatchView />
        </PlanGuard>
      ) },
      { path: '/dashboard/company-analysis', element: (
        <PlanGuard requiredPlan="PRO">
          <CompanyAnalysisView />
        </PlanGuard>
      ) },
      { path: '/dashboard/jd-insights', element: (
        <PlanGuard requiredPlan="PRO">
          <JdInsightsView />
        </PlanGuard>
      ) },
      { path: '/dashboard/company-dna', element: (
        <PlanGuard requiredPlan="PRO">
          <CompanyDnaView />
        </PlanGuard>
      ) },
      { path: '/dashboard/company-compare', element: (
        <PlanGuard requiredPlan="PRO">
          <CompanyCompareView />
        </PlanGuard>
      ) },

      // User panel (/my) - placeholder pages for Phase 5
      { path: '/my/profile', element: <ProfilePage /> },
      { path: '/my/billing', element: <BillingPage /> },
      { path: '/my/billing/plans', element: <PlansPage /> },
      { path: '/my/billing/history', element: <PlaceholderPage title="결제 이력" /> },
      { path: '/my/billing/payment-methods', element: <PlaceholderPage title="결제 수단 관리" /> },
      { path: '/my/analytics', element: <PlaceholderPage title="사용 분석" /> },
      { path: '/my/analytics/usage', element: <PlaceholderPage title="사용량 통계" /> },
      { path: '/my/analytics/history', element: <PlaceholderPage title="활동 타임라인" /> },
      { path: '/my/analytics/search', element: <PlaceholderPage title="검색 히스토리" /> },
      { path: '/my/settings', element: <SettingsPage /> },
      { path: '/my/delete-account', element: <PlaceholderPage title="회원 탈퇴" /> },

      // Admin panel routes - each wrapped with RoleGuard
      {
        path: '/admin/users',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="유저 관리" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/users/:id',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="유저 상세" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/traffic',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="트래픽 모니터링" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/billing',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="과금 관리" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/categories',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="카테고리 관리" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/ga',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="GA 대시보드" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/data',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="데이터 조회" />
          </RoleGuard>
        ),
      },
      {
        path: '/admin/settings',
        element: (
          <RoleGuard requiredRole="SUPER_ADMIN">
            <PlaceholderPage title="시스템 설정" />
          </RoleGuard>
        ),
      },
    ],
  },

  // Landing page (public)
  { path: '/', element: <LandingPage /> },

  // 404
  {
    path: '*',
    element: (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
          <p className="text-gray-500 mb-4">페이지를 찾을 수 없습니다.</p>
          <a href="/dashboard" className="text-gray-900 underline hover:no-underline">대시보드로 이동</a>
        </div>
      </div>
    ),
  },
]);
