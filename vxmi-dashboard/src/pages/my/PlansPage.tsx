import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { apiClient } from '../../services/apiClient';
import { initTossPayments } from '../../services/tossPayments';
import type { PreparePaymentResponse } from '../../services/tossPayments';
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

  // STARTER → 즉시 변경 (결제 없음)
  const handleUpgradeToStarter = async () => {
    setUpgradingPlan('STARTER');
    try {
      const response = await apiClient.post<{
        status: string;
        data: { id: string; plan: BusinessPlan; status: string; startedAt: string; expiresAt: string };
        message: string;
      }>('/api/v1/subscriptions/upgrade', { plan: 'STARTER' });

      if (user) {
        setUser({ ...user, plan: response.data.data.plan });
      }
      alert(response.data.message ?? '플랜이 Starter로 변경되었습니다.');
    } catch (err: unknown) {
      const axiosData = (err as { response?: { data?: { detail?: string } } })?.response?.data;
      const message = axiosData?.detail ?? '플랜 변경에 실패했습니다. 다시 시도해 주세요.';
      alert(message);
    } finally {
      setUpgradingPlan(null);
    }
  };

  // PRO / ENTERPRISE → Toss 결제 플로우
  const handleUpgradeWithPayment = async (planId: BusinessPlan) => {
    setUpgradingPlan(planId);
    try {
      // 1. 결제 준비 — 서버에서 orderId, amount 발급
      const prepareRes = await apiClient.post<{
        status: string;
        data: PreparePaymentResponse;
        message: string | null;
      }>('/api/v1/payments/prepare', { plan: planId });

      const { orderId, amount, orderName } = prepareRes.data.data;

      // 2. Toss Payments SDK 초기화 → payment 객체 생성
      const tossPayments = await initTossPayments();
      if (!tossPayments) {
        alert('결제 모듈을 불러올 수 없습니다. VITE_TOSS_CLIENT_KEY를 확인해 주세요.');
        return;
      }

      // 비회원 결제 (customerKey 없이 ANONYMOUS 사용)
      const { ANONYMOUS } = await import('@tosspayments/tosspayments-sdk');
      const payment = tossPayments.payment({ customerKey: ANONYMOUS });

      // 3. 결제창 열기 — 성공/실패 시 해당 URL로 리다이렉트
      const baseUrl = window.location.origin;
      await payment.requestPayment({
        method: 'CARD',
        amount: {
          currency: 'KRW',
          value: amount,
        },
        orderId,
        orderName,
        successUrl: `${baseUrl}/my/billing/payment/success`,
        failUrl: `${baseUrl}/my/billing/payment/fail`,
        customerEmail: user?.email ?? '',
        customerName: user?.name ?? '',
      });
      // requestPayment는 리다이렉트로 완료되므로 이후 코드는 실행되지 않음
    } catch (err: unknown) {
      // Toss SDK 에러 (사용자 취소 포함)
      const tossErr = err as { code?: string; message?: string };
      if (tossErr.code === 'PAY_PROCESS_CANCELED') {
        return; // 사용자가 결제창을 닫음 — 무시
      }
      if (tossErr.code) {
        alert(`결제 오류: ${tossErr.message ?? '알 수 없는 오류'}`);
        return;
      }
      // Axios 에러 처리
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const message = axiosErr?.response?.data?.detail ?? '결제 처리 중 오류가 발생했습니다.';
      alert(message);
    } finally {
      setUpgradingPlan(null);
    }
  };

  const handleUpgrade = async (planId: BusinessPlan) => {
    if (isDowngrade(planId)) {
      alert('다운그레이드는 지원하지 않습니다. 고객센터에 문의해 주세요.');
      return;
    }

    if (planId === 'STARTER') {
      await handleUpgradeToStarter();
    } else {
      await handleUpgradeWithPayment(planId);
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
                  : plan.id === 'STARTER'
                  ? '다운그레이드'
                  : '결제하기'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
