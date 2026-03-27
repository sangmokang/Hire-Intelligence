import { Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import type { PlanType } from '../../types/auth';

const PLAN_LABEL: Record<PlanType, string> = {
  TALENT_FREE: 'Talent 무료',
  TALENT_PLUS: 'Talent Plus',
  STARTER: 'Starter',
  PRO: 'Pro',
  ENTERPRISE: 'Enterprise',
};

const PLAN_FEATURES: Record<PlanType, string[]> = {
  TALENT_FREE: ['기본 채용 공고 조회', '상위 기업 분석 (제한)'],
  TALENT_PLUS: ['전체 채용 공고 조회', '상위 기업 분석', '이력서 매칭'],
  STARTER: ['상위 기업 분석', 'SD 매트릭스', '기본 대시보드'],
  PRO: ['모든 Starter 기능', '타임라인 분석', '채용 트렌드', '이력서 매칭', '기업 심층 분석'],
  ENTERPRISE: ['모든 Pro 기능', '전용 지원', '커스텀 리포트', 'API 접근', '무제한 시트'],
};

const PLAN_STATUS_COLOR: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-gray-100 text-gray-600',
};

export default function BillingPage() {
  const { user } = useAuthStore();

  if (!user) return null;

  const planStatus = 'active'; // 실제 구현 시 BE에서 가져옴
  const features = PLAN_FEATURES[user.plan] ?? [];

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">결제 관리</h1>
        <p className="text-sm text-gray-500 mt-1">현재 구독 플랜과 결제 이력을 확인하세요.</p>
      </div>

      {/* 현재 플랜 카드 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900">현재 플랜</h2>
            <p className="text-2xl font-bold text-gray-900 mt-1">{PLAN_LABEL[user.plan]}</p>
          </div>
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${PLAN_STATUS_COLOR[planStatus]}`}>
            {planStatus === 'active' ? '활성' : '비활성'}
          </span>
        </div>

        <div>
          <p className="text-xs text-gray-500 mb-2">포함 기능</p>
          <ul className="space-y-1">
            {features.map((feature) => (
              <li key={feature} className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {feature}
              </li>
            ))}
          </ul>
        </div>

        <Link
          to="/my/billing/plans"
          className="inline-block w-full sm:w-auto text-center px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
        >
          요금제 변경
        </Link>
      </div>

      {/* 결제 이력 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">결제 이력</h2>
        <div className="flex flex-col items-center justify-center py-10 text-gray-400">
          <svg className="w-10 h-10 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm">결제 이력이 없습니다.</p>
        </div>
      </div>
    </div>
  );
}
