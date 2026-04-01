import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../../stores/authStore';
import { useUIStore } from '../../stores/uiStore';
import { hasPermission } from '../../types/auth';
import { apiClient } from '../../services/apiClient';
import { trackEvent } from '../../lib/analytics';
import logo from '../../assets/logo.svg';

// ── Inline SVG icons ──────────────────────────────────────────────────────────

function IconChart() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.5h4.5v7.5H3v-7.5zm6.75-6h4.5v13.5h-4.5V7.5zm6.75 3.75h4.5v9.75h-4.5V11.25z" />
    </svg>
  );
}

function IconGrid() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zm0 9.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zm9.75-9.75A2.25 2.25 0 0115.75 3.75H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zm0 9.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  );
}

function IconClock() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function IconTrendUp() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
    </svg>
  );
}

function IconDocument() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

function IconBuilding() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
    </svg>
  );
}

function IconUser() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
  );
}

function IconCreditCard() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
    </svg>
  );
}

function IconAnalytics() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
    </svg>
  );
}

function IconCog() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function IconUsers() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
    </svg>
  );
}

function IconSignal() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}

function IconTag() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
    </svg>
  );
}

function IconDatabase() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
    </svg>
  );
}

function IconGlobe() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253M3 12a8.959 8.959 0 01.284-2.253" />
    </svg>
  );
}

function IconMenu() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
    </svg>
  );
}

function IconLogout() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
    </svg>
  );
}

function IconChevronDown() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

// ── Role badge ────────────────────────────────────────────────────────────────

const ROLE_LABEL: Record<string, string> = {
  SUPER_ADMIN: '관리자',
  USER: '사용자',
  GUEST: '게스트',
};

const ROLE_COLOR: Record<string, string> = {
  SUPER_ADMIN: 'bg-purple-500/20 text-purple-300',
  USER: 'bg-blue-500/20 text-blue-300',
  GUEST: 'bg-gray-500/20 text-gray-400',
};

// ── Nav item helpers ──────────────────────────────────────────────────────────

function IconLockSmall() {
  return (
    <svg className="w-3 h-3 text-gray-500 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
  );
}

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
  proOnly?: boolean;
}

const ANALYSIS_NAV: NavItem[] = [
  { label: 'Top 20 채용 볼륨', to: '/dashboard/top-companies', icon: <IconChart /> },
  { label: '수요공급 매트릭스', to: '/dashboard/sd-matrix', icon: <IconGrid /> },
  { label: '시계열 인텔리전스', to: '/dashboard/timeline', icon: <IconClock />, proOnly: true },
  { label: '채용 트렌드', to: '/dashboard/trends', icon: <IconTrendUp />, proOnly: true },
  { label: '이력서 매칭', to: '/dashboard/resume-match', icon: <IconDocument />, proOnly: true },
  { label: '기업 분석', to: '/dashboard/company-analysis', icon: <IconBuilding />, proOnly: true },
  { label: 'JD 인사이트', to: '/dashboard/jd-insights', icon: <IconDocument />, proOnly: true },
  { label: '회사 DNA', to: '/dashboard/company-dna', icon: <IconBuilding />, proOnly: true },
  { label: '기업 비교', to: '/dashboard/company-compare', icon: <IconBuilding />, proOnly: true },
];

const MY_NAV: NavItem[] = [
  { label: '내 프로필', to: '/my/profile', icon: <IconUser /> },
  { label: '결제 관리', to: '/my/billing', icon: <IconCreditCard /> },
  { label: '사용 분석', to: '/my/analytics', icon: <IconAnalytics /> },
  { label: '설정', to: '/my/settings', icon: <IconCog /> },
];

const ADMIN_NAV: NavItem[] = [
  { label: '유저 관리', to: '/admin/users', icon: <IconUsers /> },
  { label: '트래픽 모니터링', to: '/admin/traffic', icon: <IconSignal /> },
  { label: '과금 관리', to: '/admin/billing', icon: <IconCreditCard /> },
  { label: '카테고리 관리', to: '/admin/categories', icon: <IconTag /> },
  { label: 'GA 대시보드', to: '/admin/ga', icon: <IconGlobe /> },
  { label: '데이터 조회', to: '/admin/data', icon: <IconDatabase /> },
];

function NavSection({ title, items, isStarterUser }: { title: string; items: NavItem[]; isStarterUser?: boolean }) {
  return (
    <div className="mb-6">
      <p className="px-3 mb-1 text-[10px] font-semibold tracking-widest uppercase text-gray-500">
        {title}
      </p>
      <ul className="space-y-0.5">
        {items.map((item) => {
          const locked = isStarterUser && item.proOnly;
          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end
                onClick={() => {
                  // 사이드바 네비게이션 클릭 이벤트 GA4 전송
                  trackEvent('Navigation', 'click_sidebar_nav', item.label);
                }}
                className={({ isActive }) =>
                  [
                    'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors',
                    isActive
                      ? 'bg-white/10 text-white font-medium'
                      : 'text-gray-400 hover:text-white hover:bg-white/5',
                  ].join(' ')
                }
              >
                {item.icon}
                <span className="flex-1">{item.label}</span>
                {locked && <IconLockSmall />}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ── Dashboard metadata hook ───────────────────────────────────────────────────

function useDashboardMetadata() {
  return useQuery({
    queryKey: ['dashboard', 'metadata'] as const,
    queryFn: async () => {
      const res = await apiClient.get<{ data: { latestWeek: string | null; updatedAt: string | null } }>(
        '/api/v1/dashboard/metadata'
      );
      return res.data.data;
    },
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: false,
  });
}

// ── Main layout ───────────────────────────────────────────────────────────────

export function DashboardLayout() {
  const { user, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUIStore();
  const navigate = useNavigate();
  const { data: metadata } = useDashboardMetadata();

  const isAdmin = user ? hasPermission(user.role, 'SUPER_ADMIN') : false;
  const isUser = user ? hasPermission(user.role, 'USER') : false;
  // STARTER 플랜 사용자 여부 (Pro 이상이 아닌 경우)
  const isStarterUser = !user?.plan || user.plan === 'STARTER' || user.plan === 'TALENT_FREE' || user.plan === 'TALENT_PLUS';

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ── */}
      <aside
        style={{ backgroundColor: '#191918' }}
        className={[
          'fixed inset-y-0 left-0 z-30 flex flex-col w-64 transition-transform duration-200',
          'lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-white/10 shrink-0">
          <img src={logo} alt="VXMI" className="h-7 w-auto" />
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-2 py-4">
          <NavSection title="분석" items={ANALYSIS_NAV} isStarterUser={isStarterUser} />
          {isUser && <NavSection title="내 계정" items={MY_NAV} />}
          {isAdmin && <NavSection title="관리자" items={ADMIN_NAV} />}
        </nav>

        {/* User info */}
        {user && (
          <div className="border-t border-white/10 px-3 py-3 shrink-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
                <span
                  className={[
                    'mt-1 inline-block px-1.5 py-0.5 rounded text-[10px] font-medium',
                    ROLE_COLOR[user.role] ?? ROLE_COLOR.GUEST,
                  ].join(' ')}
                >
                  {ROLE_LABEL[user.role] ?? user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="로그아웃"
                className="mt-0.5 p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors shrink-0"
              >
                <IconLogout />
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* ── Main column ── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex items-center h-16 px-4 bg-white border-b border-gray-200 shrink-0 gap-3">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="사이드바 토글"
          >
            <IconMenu />
          </button>

          {/* Title area — can be populated by child pages via a context/store later */}
          <div className="flex-1" />

          {/* 데이터 갱신 기준 주차 표시 */}
          {metadata?.latestWeek && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 rounded-md bg-gray-100 text-xs text-gray-500 font-medium">
              <span>📊</span>
              <span>{metadata.latestWeek} 기준</span>
            </span>
          )}

          {/* User avatar + dropdown */}
          {user && (
            <div className="relative group">
              <button className="flex items-center gap-2 p-1.5 rounded-md hover:bg-gray-100 transition-colors">
                <div className="w-7 h-7 rounded-full bg-gray-300 flex items-center justify-center text-xs font-semibold text-gray-700 overflow-hidden">
                  {user.profileImageUrl ? (
                    <img src={user.profileImageUrl} alt={user.name} className="w-full h-full object-cover" />
                  ) : (
                    user.name.charAt(0).toUpperCase()
                  )}
                </div>
                <span className="hidden sm:block text-sm font-medium text-gray-700">{user.name}</span>
                <IconChevronDown />
              </button>

              {/* Dropdown */}
              <div className="absolute right-0 mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-100 py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
                <NavLink
                  to="/my/profile"
                  className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <IconUser />
                  내 프로필
                </NavLink>
                <hr className="my-1 border-gray-100" />
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <IconLogout />
                  로그아웃
                </button>
              </div>
            </div>
          )}
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
