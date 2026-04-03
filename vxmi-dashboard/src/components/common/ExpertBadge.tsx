/**
 * 전문가 배지 컴포넌트 — 전문가 이름 + 도메인 색상 표시
 */

// 전문가별 색상 매핑
const EXPERT_COLORS: Record<string, string> = {
  CFO: 'bg-blue-100 text-blue-700',
  CIO: 'bg-indigo-100 text-indigo-700',
  QA: 'bg-green-100 text-green-700',
  CTO: 'bg-purple-100 text-purple-700',
  UX: 'bg-pink-100 text-pink-700',
  UI: 'bg-rose-100 text-rose-700',
  USER_RESEARCHER: 'bg-fuchsia-100 text-fuchsia-700',
  ML_ENGINEER: 'bg-orange-100 text-orange-700',
  DATA_SCIENTIST: 'bg-cyan-100 text-cyan-700',
  BIZ_DATA_ANALYST: 'bg-teal-100 text-teal-700',
  CPO: 'bg-violet-100 text-violet-700',
  CISO: 'bg-red-100 text-red-700',
  FRONTEND_LEAD: 'bg-sky-100 text-sky-700',
  BACKEND_LEAD: 'bg-emerald-100 text-emerald-700',
  INFRA: 'bg-slate-100 text-slate-700',
  BRAND_MANAGER: 'bg-amber-100 text-amber-700',
  MARKETER: 'bg-lime-100 text-lime-700',
  GROWTH_MARKETER: 'bg-yellow-100 text-yellow-700',
};

interface ExpertBadgeProps {
  expert: string;
  expertName: string;
  size?: 'sm' | 'md';
}

export function ExpertBadge({ expert, expertName, size = 'md' }: ExpertBadgeProps) {
  const color = EXPERT_COLORS[expert] ?? 'bg-gray-100 text-gray-700';
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${color} ${sizeClass}`}>
      {expertName}
    </span>
  );
}
