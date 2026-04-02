import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/apiClient';
import { useAuthStore } from '../../stores/authStore';
import type { BusinessPlan } from '../../types/auth';

interface ConfirmPaymentData {
  paymentKey: string;
  orderId: string;
  amount: number;
  status: string;
  approvedAt: string;
}

interface ConfirmPaymentResponse {
  status: string;
  data: ConfirmPaymentData & { plan?: BusinessPlan };
  message: string | null;
}

type PageState = 'loading' | 'success' | 'error';

export default function PaymentSuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, setUser } = useAuthStore();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [paymentData, setPaymentData] = useState<ConfirmPaymentData | null>(null);

  useEffect(() => {
    const paymentKey = searchParams.get('paymentKey');
    const orderId = searchParams.get('orderId');
    const amountStr = searchParams.get('amount');

    if (!paymentKey || !orderId || !amountStr) {
      setErrorMessage('결제 정보가 올바르지 않습니다.');
      setPageState('error');
      return;
    }

    const amount = parseInt(amountStr, 10);

    void (async () => {
      try {
        const response = await apiClient.post<ConfirmPaymentResponse>(
          '/api/v1/payments/confirm',
          { paymentKey, orderId, amount }
        );

        setPaymentData(response.data.data);

        // 결제 완료 후 유저 플랜 갱신
        if (user && response.data.data.plan) {
          setUser({ ...user, plan: response.data.data.plan });
        }

        setPageState('success');
      } catch (err: unknown) {
        const axiosData = (err as { response?: { data?: { detail?: string } } })?.response?.data;
        setErrorMessage(axiosData?.detail ?? '결제 확인 중 오류가 발생했습니다.');
        setPageState('error');
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (pageState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-900 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">결제를 확인하고 있습니다...</p>
        </div>
      </div>
    );
  }

  if (pageState === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white rounded-xl shadow-md p-8 max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900">결제 확인 실패</h1>
          <p className="text-gray-500 text-sm">{errorMessage}</p>
          <button
            onClick={() => void navigate('/my/billing/plans')}
            className="w-full py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
          >
            요금제 페이지로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-md p-8 max-w-md w-full text-center space-y-4">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
          <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900">결제가 완료되었습니다!</h1>
        {paymentData && (
          <div className="bg-gray-50 rounded-lg p-4 text-left space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>주문 번호</span>
              <span className="font-medium text-gray-900">{paymentData.orderId}</span>
            </div>
            <div className="flex justify-between">
              <span>결제 금액</span>
              <span className="font-medium text-gray-900">₩{paymentData.amount.toLocaleString()}</span>
            </div>
          </div>
        )}
        <p className="text-gray-500 text-sm">플랜이 즉시 활성화됩니다.</p>
        <button
          onClick={() => void navigate('/dashboard')}
          className="w-full py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
        >
          대시보드로 이동
        </button>
      </div>
    </div>
  );
}
