import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../services/apiClient';

interface BillingKeyResponse {
  id: string;
  customerKey: string;
  cardLastFour: string;
  cardCompany: string;
  isDefault: boolean;
  createdAt: string;
}

interface ApiResponse<T> {
  status: string;
  data: T;
  message: string | null;
}

// 카드 목록 조회
async function fetchPaymentMethods(): Promise<BillingKeyResponse[]> {
  const { data } = await apiClient.get<ApiResponse<BillingKeyResponse[]>>(
    '/api/v1/payments/methods'
  );
  return data.data;
}

// 카드 삭제
async function deletePaymentMethod(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/payments/methods/${id}`);
}

// 카드 추가 (mock 데이터로 POST)
async function addPaymentMethod(payload: {
  customerKey: string;
  billingKey: string;
  cardLastFour: string;
  cardCompany: string;
}): Promise<BillingKeyResponse> {
  const { data } = await apiClient.post<ApiResponse<BillingKeyResponse>>(
    '/api/v1/payments/methods',
    payload
  );
  return data.data;
}

export default function PaymentMethodsPage() {
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  // 카드 목록 조회
  const { data: methods = [], isLoading } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: fetchPaymentMethods,
  });

  // 카드 삭제 뮤테이션
  const deleteMutation = useMutation({
    mutationFn: deletePaymentMethod,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
    },
  });

  // 카드 추가 뮤테이션 (mock 데이터)
  const addMutation = useMutation({
    mutationFn: addPaymentMethod,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] });
      setShowAddForm(false);
      setAddError(null);
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? '카드 등록에 실패했습니다.';
      setAddError(detail);
    },
  });

  // 목(mock) 카드 추가 — Toss billingAuth SDK 연동 전 임시
  const handleAddMock = () => {
    const mockSuffix = String(Math.floor(1000 + Math.random() * 9000));
    addMutation.mutate({
      customerKey: `cust_${Date.now()}`,
      billingKey: `auth_${Date.now()}`,
      cardLastFour: mockSuffix,
      cardCompany: '신한카드',
    });
  };

  const handleDelete = (id: string) => {
    if (!confirm('이 결제 수단을 삭제하시겠습니까?')) return;
    deleteMutation.mutate(id);
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">결제 수단 관리</h1>
          <p className="text-sm text-gray-500 mt-1">
            등록된 카드를 확인하고 관리하세요.
          </p>
        </div>
        <button
          onClick={() => {
            setShowAddForm((v) => !v);
            setAddError(null);
          }}
          className="px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors"
        >
          카드 추가
        </button>
      </div>

      {/* 카드 추가 패널 */}
      {showAddForm && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-3">
          <h2 className="text-base font-semibold text-gray-900">새 카드 등록</h2>
          <p className="text-sm text-gray-500">
            Toss billingAuth SDK 연동 전 목(mock) 데이터로 등록됩니다.
          </p>
          {addError && (
            <p className="text-sm text-red-600">{addError}</p>
          )}
          <div className="flex gap-2">
            <button
              onClick={handleAddMock}
              disabled={addMutation.isPending}
              className="px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {addMutation.isPending ? '등록 중...' : '테스트 카드 등록'}
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
          </div>
        </div>
      )}

      {/* 카드 목록 */}
      <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-sm text-gray-400">불러오는 중...</p>
          </div>
        ) : methods.length === 0 ? (
          /* 빈 상태 */
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
              <svg
                className="w-6 h-6 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-700">
              등록된 결제 수단이 없습니다.
            </p>
            <p className="text-xs text-gray-400 mt-1">
              위 버튼을 눌러 카드를 추가하세요.
            </p>
          </div>
        ) : (
          methods.map((method) => (
            <div
              key={method.id}
              className="flex items-center justify-between px-5 py-4"
            >
              <div className="flex items-center gap-3">
                {/* 카드 아이콘 */}
                <div className="w-10 h-7 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {method.cardCompany}{' '}
                    <span className="font-mono">****{method.cardLastFour}</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(method.createdAt).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}{' '}
                    등록
                  </p>
                </div>
                {method.isDefault && (
                  <span className="ml-2 inline-block text-xs font-medium bg-gray-900 text-white px-2 py-0.5 rounded-full">
                    기본
                  </span>
                )}
              </div>
              <button
                onClick={() => handleDelete(method.id)}
                disabled={deleteMutation.isPending}
                className="text-sm text-red-500 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                삭제
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
