import type { BillingHistoryItem } from '../../services/userService';

// mock 데이터 inline (결제 시스템 미구현)
const MOCK_BILLING_HISTORY: BillingHistoryItem[] = [
  { id: 'inv-001', date: '2026-03-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-002', date: '2026-02-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-003', date: '2026-01-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-004', date: '2025-12-01', amount: 0, plan: 'Starter', status: '무료' },
];

const STATUS_COLOR: Record<string, string> = {
  완료: 'bg-green-100 text-green-700',
  무료: 'bg-gray-100 text-gray-600',
  실패: 'bg-red-100 text-red-700',
  대기: 'bg-yellow-100 text-yellow-700',
};

export default function BillingHistoryPage() {
  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">결제 이력</h1>
        <p className="text-sm text-gray-500 mt-1">과거 결제 내역을 확인하세요.</p>
      </div>

      {/* 준비 중 안내 배너 */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4">
        <svg
          className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div>
          <p className="text-sm font-medium text-blue-800">결제 시스템 준비 중입니다</p>
          <p className="text-xs text-blue-600 mt-0.5">
            실제 결제 연동이 완료되면 정확한 결제 내역이 표시됩니다. 현재는 샘플 데이터가 표시됩니다.
          </p>
        </div>
      </div>

      {/* 결제 이력 테이블 */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                날짜
              </th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                플랜
              </th>
              <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                금액
              </th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                상태
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {MOCK_BILLING_HISTORY.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-700">
                  {new Date(item.date).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </td>
                <td className="px-4 py-3 text-gray-700 font-medium">{item.plan}</td>
                <td className="px-4 py-3 text-right text-gray-900 font-semibold">
                  {item.amount === 0 ? '무료' : `₩${item.amount.toLocaleString()}`}
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLOR[item.status] ?? 'bg-gray-100 text-gray-600'}`}
                  >
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
