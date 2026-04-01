/** 구독/요금제 관련 타입 */

// 구독 상태
export type SubscriptionStatus = 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'TRIAL';

// 현재 구독 정보
export interface SubscriptionResponse {
  id: string;
  plan: string;
  status: SubscriptionStatus;
  startedAt: string;
  expiresAt?: string;
}

// 요금제 정보
export interface PlanInfo {
  name: string;
  displayName: string;
  price: number;
  currency: string;
  billingPeriod: string;
  features: string[];
  isPopular: boolean;
}

// 요금제 목록 응답
export interface PlansListResponse {
  plans: PlanInfo[];
}
