import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../../services/apiClient'
import { useAuthStore } from '../../stores/authStore'
import type { OppAlertItem, OppAlertListResponse } from '../../types/oppAlert'

// ── 우선순위 색상/스타일 ───────────────────────────────────────────────────────

type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM'

const PRIORITY_BORDER: Record<Priority, string> = {
  CRITICAL: 'border-l-4 border-l-red-500',
  HIGH: 'border-l-4 border-l-orange-500',
  MEDIUM: 'border-l-4 border-l-yellow-500',
}

const PRIORITY_BADGE: Record<Priority, string> = {
  CRITICAL: 'bg-red-100 text-red-700',
  HIGH: 'bg-orange-100 text-orange-700',
  MEDIUM: 'bg-yellow-100 text-yellow-700',
}

const PRIORITY_LABEL: Record<Priority, string> = {
  CRITICAL: 'CRITICAL',
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
}

// ── S/D Ratio 신호등 ─────────────────────────────────────────────────────────

function SdRatioLight({ ratio }: { ratio: number }) {
  let color = 'bg-green-500'
  let label = '공급 우위'
  if (ratio < 0.5) {
    color = 'bg-red-500'
    label = '공급 희소'
  } else if (ratio < 1.0) {
    color = 'bg-yellow-500'
    label = '균형'
  }
  return (
    <div className="flex items-center gap-1.5">
      <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${color}`} />
      <span className="text-xs text-gray-500">S/D {ratio.toFixed(2)} ({label})</span>
    </div>
  )
}

// ── OppScore 게이지 바 ────────────────────────────────────────────────────────

function OppScoreBar({ score, priority }: { score: number; priority: Priority }) {
  const barColor: Record<Priority, string> = {
    CRITICAL: 'bg-red-500',
    HIGH: 'bg-orange-500',
    MEDIUM: 'bg-yellow-500',
  }
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500">OppScore</span>
        <span className="text-xs font-bold text-gray-800">{score}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor[priority]}`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
    </div>
  )
}

// ── 트리거 데이터 ─────────────────────────────────────────────────────────────

function TriggerChips({ triggers }: { triggers: OppAlertItem['triggers'] }) {
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
        신규공고 {triggers.newPostings}건
      </span>
      <span className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">
        채용 {triggers.hiringWeeks}주 연속
      </span>
      {triggers.otwIncrease > 0 && (
        <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
          OTW +{triggers.otwIncrease}%
        </span>
      )}
    </div>
  )
}

// ── 알림 카드 ─────────────────────────────────────────────────────────────────

function AlertCard({ item }: { item: OppAlertItem }) {
  const priority = item.priority as Priority
  return (
    <div
      className={[
        'bg-white rounded-xl border border-gray-200 shadow-sm p-4',
        PRIORITY_BORDER[priority],
      ].join(' ')}
    >
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-semibold text-gray-900 text-sm truncate">{item.companyName}</span>
          <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded shrink-0">
            {item.segment}
          </span>
        </div>
        <span
          className={[
            'text-xs font-bold px-2 py-0.5 rounded shrink-0',
            PRIORITY_BADGE[priority],
          ].join(' ')}
        >
          {PRIORITY_LABEL[priority]}
        </span>
      </div>

      {/* S/D Ratio 신호등 */}
      <SdRatioLight ratio={item.triggers.sdRatio} />

      {/* OppScore 게이지 */}
      <OppScoreBar score={item.oppScore} priority={priority} />

      {/* 트리거 칩 */}
      <TriggerChips triggers={item.triggers} />

      {/* 감지 시각 */}
      <p className="text-xs text-gray-400 mt-2">
        감지: {new Date(item.detectedAt).toLocaleString('ko-KR')}
      </p>
    </div>
  )
}

// ── 빈 상태 ──────────────────────────────────────────────────────────────────

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  )
}

// ── 메인 뷰 ──────────────────────────────────────────────────────────────────

type FilterPriority = 'ALL' | Priority

const PRIORITY_FILTER_OPTIONS: { value: FilterPriority; label: string }[] = [
  { value: 'ALL', label: '전체' },
  { value: 'CRITICAL', label: 'CRITICAL' },
  { value: 'HIGH', label: 'HIGH' },
  { value: 'MEDIUM', label: 'MEDIUM' },
]

async function fetchOppAlerts(): Promise<OppAlertListResponse> {
  const res = await apiClient.get<{ status: string; data: OppAlertListResponse }>('/api/v1/opp-alert')
  return res.data.data
}

export function OppAlertView() {
  const user = useAuthStore(s => s.user)
  const [priorityFilter, setPriorityFilter] = useState<FilterPriority>('ALL')
  const [segmentFilter, setSegmentFilter] = useState<string>('ALL')

  const { data, isLoading, error } = useQuery({
    queryKey: ['oppAlert'],
    queryFn: fetchOppAlerts,
    staleTime: 1000 * 60 * 5, // 5분
  })

  const isHeadhunter = user?.category === 'HEADHUNTER'

  // 세그먼트 목록 추출
  const segments = data
    ? ['ALL', ...Array.from(new Set(data.items.map(i => i.segment))).filter(Boolean)]
    : ['ALL']

  // 필터 적용
  const filtered = (data?.items ?? []).filter(item => {
    if (priorityFilter !== 'ALL' && item.priority !== priorityFilter) return false
    if (segmentFilter !== 'ALL' && item.segment !== segmentFilter) return false
    return true
  })

  const mainContent = (
    <div className="p-6">
      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-gray-900">OppAlert 피드</h1>
            <span className="text-xs font-medium bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
              헤드헌터 전용
            </span>
          </div>
          <p className="mt-0.5 text-sm text-gray-500">
            채용 시그널 기반 BD 기회 자동 감지 — OppScore 30점 이상 기업만 표시
          </p>
        </div>
      </div>

      {/* 필터 바 */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        {/* 우선순위 필터 */}
        <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
          {PRIORITY_FILTER_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setPriorityFilter(opt.value)}
              className={[
                'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                priorityFilter === opt.value
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* 세그먼트 필터 */}
        <select
          value={segmentFilter}
          onChange={e => setSegmentFilter(e.target.value)}
          className="text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-300"
        >
          {segments.map(seg => (
            <option key={seg} value={seg}>
              {seg === 'ALL' ? '전체 세그먼트' : seg}
            </option>
          ))}
        </select>

        {data && (
          <span className="text-xs text-gray-400 ml-auto">
            총 {filtered.length}개 기회 감지됨
          </span>
        )}
      </div>

      {/* 카드 리스트 */}
      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <EmptyState message="데이터를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요." />
      )}

      {!isLoading && !error && filtered.length === 0 && (
        <EmptyState
          message={
            data && data.total === 0
              ? '분석 중입니다. 데이터가 수집되면 자동으로 표시됩니다.'
              : '선택한 필터 조건에 해당하는 기업이 없습니다.'
          }
        />
      )}

      {!isLoading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(item => (
            <AlertCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  )

  // 헤드헌터가 아닌 경우 blur 오버레이 표시
  if (!isHeadhunter) {
    return (
      <div className="relative">
        <div className="blur-sm pointer-events-none select-none">
          {mainContent}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 px-8 py-6 text-center max-w-sm">
            <div className="w-12 h-12 rounded-full bg-indigo-50 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-gray-900 mb-1">헤드헌터 전용 뷰</h2>
            <p className="text-sm text-gray-500">
              이 뷰는 헤드헌터 전용입니다. 계정 카테고리를 확인하세요.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return mainContent
}
