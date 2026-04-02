import { useState, useEffect } from 'react'
import {
  fetchBillingSummary,
  fetchBillingPayments,
  type PlanStat,
  type PaymentItem,
} from '../../services/adminApi'
import { formatDate } from '../../utils/format'

// 금액 포맷 헬퍼
function formatAmount(amount: number): string {
  return amount.toLocaleString('ko-KR') + '원'
}

// 결제 상태 배지
function PaymentStatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    PAID: 'bg-green-100 text-green-700',
    PENDING: 'bg-yellow-100 text-yellow-700',
    FAILED: 'bg-red-100 text-red-700',
    CANCELLED: 'bg-gray-100 text-gray-500',
    REFUNDED: 'bg-blue-100 text-blue-700',
  }
  const labelMap: Record<string, string> = {
    PAID: '결제완료',
    PENDING: '대기중',
    FAILED: '실패',
    CANCELLED: '취소',
    REFUNDED: '환불',
  }
  const cls = colorMap[status] ?? 'bg-gray-100 text-gray-500'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {labelMap[status] ?? status}
    </span>
  )
}

// 플랜별 분포 색상
const PLAN_COLORS: Record<string, string> = {
  STARTER: 'bg-gray-400',
  PRO: 'bg-blue-500',
  ENTERPRISE: 'bg-purple-500',
}

const LIMIT = 20

export function AdminBillingView() {
  // 요약 상태
  const [planStats, setPlanStats] = useState<PlanStat[]>([])
  const [totalUsers, setTotalUsers] = useState(0)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  // 결제 내역 상태
  const [payments, setPayments] = useState<PaymentItem[]>([])
  const [paymentsTotal, setPaymentsTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [paymentsLoading, setPaymentsLoading] = useState(false)
  const [paymentsError, setPaymentsError] = useState<string | null>(null)

  // 플랜 요약 조회
  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setSummaryLoading(true)
      setSummaryError(null)
      try {
        const res = await fetchBillingSummary()
        if (!cancelled) {
          setPlanStats(res.planStats)
          setTotalUsers(res.totalUsers)
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setSummaryError(err instanceof Error ? err.message : '요약 데이터를 불러오지 못했습니다.')
        }
      } finally {
        if (!cancelled) setSummaryLoading(false)
      }
    }
    void load()
    return () => { cancelled = true }
  }, [])

  // 결제 내역 조회 (offset 변경 시 재조회)
  useEffect(() => {
    let cancelled = false
    setPaymentsLoading(true)
    setPaymentsError(null)

    fetchBillingPayments({ offset, limit: LIMIT })
      .then((res) => {
        if (!cancelled) {
          setPayments(res.payments)
          setPaymentsTotal(res.total)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPaymentsError(err instanceof Error ? err.message : '결제 내역을 불러오지 못했습니다.')
        }
      })
      .finally(() => {
        if (!cancelled) setPaymentsLoading(false)
      })

    return () => { cancelled = true }
  }, [offset])

  const totalPages = Math.ceil(paymentsTotal / LIMIT)
  const currentPage = Math.floor(offset / LIMIT) + 1

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">과금 관리</h1>
        <p className="text-sm text-gray-500 mt-0.5">플랜 분포 및 결제 내역 조회</p>
      </div>

      {/* 플랜 분포 카드 섹션 */}
      <div className="mb-6">
        <h2 className="text-sm font-medium text-gray-700 mb-3">플랜 분포</h2>
        {summaryError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600 mb-3">
            {summaryError}
          </div>
        )}
        {summaryLoading ? (
          <div className="grid grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
                <div className="h-3 bg-gray-100 rounded w-16 mb-2" />
                <div className="h-8 bg-gray-100 rounded w-12" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {/* 전체 사용자 카드 */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs text-gray-500 mb-1">전체 사용자</p>
              <p className="text-2xl font-semibold text-gray-900">{totalUsers.toLocaleString()}</p>
              <p className="text-xs text-gray-400 mt-1">명</p>
            </div>

            {/* 플랜별 카드 */}
            {planStats.map((stat) => {
              const pct = totalUsers > 0 ? Math.round((stat.count / totalUsers) * 100) : 0
              const barColor = PLAN_COLORS[stat.plan] ?? 'bg-gray-300'
              return (
                <div key={stat.plan} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`w-2 h-2 rounded-full ${barColor}`} />
                    <p className="text-xs text-gray-500">{stat.plan}</p>
                  </div>
                  <p className="text-2xl font-semibold text-gray-900">{stat.count.toLocaleString()}</p>
                  <p className="text-xs text-gray-400 mt-1">{pct}% · 명</p>
                  {/* 비율 바 */}
                  <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${barColor}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 결제 내역 테이블 */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-700">결제 내역</h2>
          <span className="text-xs text-gray-400">총 {paymentsTotal.toLocaleString()}건</span>
        </div>

        {paymentsError && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {paymentsError}
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">유저 이메일</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">플랜</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500">금액</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">상태</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">결제일</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">생성일</th>
                </tr>
              </thead>
              <tbody>
                {paymentsLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 bg-gray-100 rounded animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : payments.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-sm text-gray-400">
                      결제 내역이 없습니다.
                    </td>
                  </tr>
                ) : (
                  payments.map((payment) => (
                    <tr key={payment.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-gray-900">{payment.userEmail ?? payment.userId}</td>
                      {/* BE에서 plan 미조인 시 "—" 표시 */}
                      <td className="px-4 py-3 text-gray-600 text-xs">{payment.plan || '—'}</td>
                      <td className="px-4 py-3 text-gray-900 text-right font-medium">{formatAmount(payment.amount)}</td>
                      <td className="px-4 py-3"><PaymentStatusBadge status={payment.status} /></td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(payment.paidAt)}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(payment.createdAt)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <span className="text-xs text-gray-500">
                {currentPage} / {totalPages} 페이지
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                  disabled={offset === 0}
                  className="text-xs px-3 py-1.5 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  이전
                </button>
                <button
                  onClick={() => setOffset(offset + LIMIT)}
                  disabled={offset + LIMIT >= paymentsTotal}
                  className="text-xs px-3 py-1.5 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
