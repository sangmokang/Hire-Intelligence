import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { apiClient } from '../../services/apiClient';
import type { BusinessPlan } from '../../types/auth';

const PLAN_ORDER: BusinessPlan[] = ['STARTER', 'PRO', 'ENTERPRISE'];

interface Plan {
  id: BusinessPlan;
  name: string;
  price: string;
  priceNote: string;
  features: string[];
}

const PLANS: Plan[] = [
  {
    id: 'STARTER',
    name: 'Starter',
    price: '무료',
    priceNote: '영구 무료',
    features: [
      '상위 기업 분석',
      'SD 매트릭스',
      '기본 대시보드',
      '월 50회 조회',
    ],
  },
  {
    id: 'PRO',
    name: 'Pro',
    price: '₩49,000',
    priceNote: '/월',
    features: [
      '모든 Starter 기능',
      '타임라인 분석',
      '채용 트렌드',
      '이력서 매칭',
      '기업 심층 분석',
      '무제한 조회',
    ],
  },
  {
    id: 'ENTERPRISE',
    name: 'Enterprise',
    price: '₩149,000',
    priceNote: '/월',
    features: [
      '모든 Pro 기능',
      '전용 고객 지원',
      '커스텀 리포트',
      'API 접근',
      '무제한 시트',
      'SLA 보장',
    ],
  },
];

export default function PlansPage() {
  const { user, setUser } = useAuthStore();
  const [upgradingPlan, setUpgradingPlan] = useState<BusinessPlan | null>(null);

  const currentPlan = user?.plan as BusinessPlan | undefined;

  const isDowngrade = (targetPlan: BusinessPlan): boolean => {
    if (!currentPlan) return false;
    const currentIdx = PLAN_ORDER.indexOf(currentPlan as BusinessPlan);
    if (currentIdx === -1) return false; // TALENT 트랙 사용자는 다운그레이드 판정 제외
    const targetIdx = PLAN_ORDER.indexOf(targetPlan);
    return targetIdx < currentIdx;
  };

  const handleUpgrade = async (planId: BusinessPlan) => {
    if (isDowngrade(planId)) {
      alert('다운그레이드는 지원하지 않습니다. 고객센터에 문의해 주세요.');
      return;
    }

    setUpgradingPlan(planId);
    try {
      const response = await apiClient.post<{
        status: string;
        data: { id: string; plan: BusinessPlan; status: string; startedAt: string; expiresAt: string };
        message: string;
      }>('/api/v1/subscriptions/upgrade', { plan: planId });

      if (user) {
        setUser({ ...user, plan: response.data.data.plan });
      }

      alert(response.data.message ?? `플랜이 ${planId}으로 변경되었습니다.`);
    } catch (err: unknown) {
      const axiosData = (err as { response?: { data?: { detail?: string } } })?.response?.data;
      const message = axiosData?.detail || '플랜 변경에 실패했습니다. 다시 시도해 주세요.';
      alert(message);
    } finally {
      setUpgradingPlan(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">요금제 비교</h1>
        <p className="text-sm text-gray-500 mt-1">나에게 맞는 플랜을 선택하세요.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {PLANS.map((plan) => {
          const isCurrent = currentPlan === plan.id;
          return (
            <div
              key={plan.id}
              className={`bg-white border rounded-xl p-6 flex flex-col space-y-4 ${
                isCurrent
                  ? 'border-gray-900 shadow-md'
                  : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{plan.name}</h2>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-2xl font-bold text-gray-900">{plan.price}</span>
                    {plan.priceNote !== '영구 무료' && (
                      <span className="text-sm text-gray-500">{plan.priceNote}</span>
                    )}
                  </div>
                  {plan.priceNote === '영구 무료' && (
                    <p className="text-xs text-gray-500 mt-0.5">{plan.priceNote}</p>
                  )}
                </div>
                {isCurrent && (
                  <span className="text-xs font-medium bg-gray-900 text-white px-2 py-1 rounded-full">
                    현재 플랜
                  </span>
                )}
              </div>

              <ul className="space-y-2 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-gray-700">
                    <svg className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => void handleUpgrade(plan.id)}
                disabled={isCurrent || upgradingPlan !== null || isDowngrade(plan.id)}
                className={`w-full py-2 text-sm font-medium rounded-lg transition-colors ${
                  isCurrent || isDowngrade(plan.id)
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-900 text-white hover:bg-gray-700 disabled:opacity-60 disabled:cursor-not-allowed'
                }`}
              >
                {upgradingPlan === plan.id
                  ? '처리 중...'
                  : isCurrent
                  ? '현재 플랜'
                  : '업그레이드'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
