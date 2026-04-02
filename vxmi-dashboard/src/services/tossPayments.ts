import { loadTossPayments } from '@tosspayments/tosspayments-sdk';

const TOSS_CLIENT_KEY = import.meta.env.VITE_TOSS_CLIENT_KEY as string | undefined ?? '';

export async function initTossPayments() {
  if (!TOSS_CLIENT_KEY) {
    console.warn('VITE_TOSS_CLIENT_KEY not set — 결제 기능이 비활성화됩니다.');
    return null;
  }
  try {
    return await loadTossPayments(TOSS_CLIENT_KEY);
  } catch (err) {
    console.error('Toss Payments SDK 로드 실패:', err);
    return null;
  }
}

export interface PreparePaymentResponse {
  orderId: string;
  amount: number;
  orderName: string;
}

export interface ConfirmPaymentResponse {
  paymentKey: string;
  orderId: string;
  amount: number;
  status: string;
}
