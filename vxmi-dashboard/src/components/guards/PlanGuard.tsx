import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import type { BusinessPlan } from '../../types/auth';

const PLAN_LEVELS: Record<BusinessPlan, number> = {
  STARTER: 0,
  PRO: 1,
  ENTERPRISE: 2,
};

interface PlanGuardProps {
  children: React.ReactNode;
  requiredPlan: BusinessPlan;
}

function IconLock() {
  return (
    <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
  );
}

export function PlanGuard({ children, requiredPlan }: PlanGuardProps) {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  // 플랜이 없거나 비즈니스 플랜이 아닌 경우 STARTER로 처리
  const userPlan = (user?.plan as BusinessPlan) ?? 'STARTER';
  const userLevel = PLAN_LEVELS[userPlan] ?? 0;
  const requiredLevel = PLAN_LEVELS[requiredPlan];

  if (userLevel < requiredLevel) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] p-8">
        <div className="text-center max-w-sm">
          <div className="flex justify-center mb-4">
            <IconLock />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            {requiredPlan} 플랜 전용 기능
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            이 기능은 {requiredPlan} 플랜 이상에서 사용할 수 있습니다.
            현재 플랜: <span className="font-medium text-gray-700">{userPlan}</span>
          </p>
          <button
            onClick={() => navigate('/my/billing/plans')}
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-md hover:bg-gray-700 transition-colors"
          >
            업그레이드
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
