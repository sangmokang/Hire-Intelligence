import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { MetricCard } from '../common/MetricCard'
import {
  MARKET_SIGNALS,
  ACTION_TEXT,
  type MarketSignalSegment,
  type PersonaType,
  type SignalLevel,
} from '../../data/marketSignals'

// ── 신호등 색상 매핑 ───────────────────────────────────────────────────────────

const SIGNAL_COLOR: Record<SignalLevel, string> = {
  RED: '#EF4444',
  YELLOW: '#F59E0B',
  GREEN: '#22C55E',
}

const SIGNAL_BG: Record<SignalLevel, string> = {
  RED: 'bg-red-50 border-red-200',
  YELLOW: 'bg-yellow-50 border-yellow-200',
  GREEN: 'bg-green-50 border-green-200',
}

const SIGNAL_LABEL: Record<SignalLevel, string> = {
  RED: '공급 희소',
  YELLOW: '균형',
  GREEN: '공급 우위',
}

// ── 추세 아이콘 ───────────────────────────────────────────────────────────────

function TrendIcon({ trend }: { trend: MarketSignalSegment['trend4w'] }) {
  if (trend === 'UP') return <span className="text-green-500 font-bold text-base leading-none">↑</span>
  if (trend === 'DOWN') return <span className="text-red-500 font-bold text-base leading-none">↓</span>
  return <span className="text-gray-400 font-bold text-base leading-none">→</span>
}

// ── 페르소나 선택 탭 ──────────────────────────────────────────────────────────

const PERSONA_OPTIONS: { value: PersonaType; label: string }[] = [
  { value: 'INHOUSE_HR', label: '인하우스 HR' },
  { value: 'HEADHUNTER', label: '헤드헌터' },
  { value: 'CHRO', label: 'CHRO' },
  { value: 'JOB_SEEKER', label: '구직자' },
]

// ── 스파크라인 차트 ───────────────────────────────────────────────────────────

function SparklineChart({ history }: { history: number[] }) {
  // 12주 히스토리를 차트 데이터로 변환
  const data = history.map((ratio, i) => ({
    week: `W-${11 - i}`,
    ratio,
  }))

  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
        <XAxis
          dataKey="week"
          tick={{ fontSize: 10, fill: '#9CA3AF' }}
          tickLine={false}
          axisLine={false}
          interval={2}
        />
        <YAxis
          domain={['auto', 'auto']}
          tick={{ fontSize: 10, fill: '#9CA3AF' }}
          tickLine={false}
          axisLine={false}
          width={32}
          tickFormatter={(v: number) => v.toFixed(1)}
        />
        <Tooltip
          formatter={(v) => [typeof v === 'number' ? v.toFixed(2) : v, 'S/D Ratio']}
          contentStyle={{
            fontSize: 11,
            padding: '4px 8px',
            border: '1px solid #E5E7EB',
            borderRadius: 6,
          }}
        />
        {/* 신호 경계선 */}
        <ReferenceLine y={0.5} stroke="#F59E0B" strokeDasharray="3 3" strokeOpacity={0.6} />
        <ReferenceLine y={1.0} stroke="#22C55E" strokeDasharray="3 3" strokeOpacity={0.6} />
        <Line
          type="monotone"
          dataKey="ratio"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// ── 세그먼트 카드 ─────────────────────────────────────────────────────────────

interface SegmentCardProps {
  segment: MarketSignalSegment
  isSelected: boolean
  onClick: () => void
}

function SegmentCard({ segment, isSelected, onClick }: SegmentCardProps) {
  return (
    <button
      onClick={onClick}
      className={[
        'text-left w-full rounded-xl border p-4 transition-all duration-150 cursor-pointer',
        'hover:shadow-md hover:-translate-y-0.5',
        isSelected
          ? 'ring-2 ring-blue-500 ring-offset-1 shadow-md'
          : SIGNAL_BG[segment.signal],
      ].join(' ')}
    >
      {/* 세그먼트명 + 신호등 */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-gray-800">{segment.name}</span>
        <span
          className="w-3 h-3 rounded-full shrink-0"
          style={{ backgroundColor: SIGNAL_COLOR[segment.signal] }}
          title={SIGNAL_LABEL[segment.signal]}
        />
      </div>

      {/* S/D Ratio */}
      <div className="flex items-end gap-1.5 mb-1">
        <span className="text-xl font-bold text-gray-900">{segment.ratio.toFixed(2)}</span>
        <span className="text-xs text-gray-500 mb-0.5">S/D</span>
      </div>

      {/* 추세 + 신호 레이블 */}
      <div className="flex items-center gap-1.5">
        <TrendIcon trend={segment.trend4w} />
        <span
          className="text-xs font-medium px-1.5 py-0.5 rounded"
          style={{
            backgroundColor: SIGNAL_COLOR[segment.signal] + '22',
            color: SIGNAL_COLOR[segment.signal],
          }}
        >
          {SIGNAL_LABEL[segment.signal]}
        </span>
      </div>
    </button>
  )
}

// ── 상세 패널 ─────────────────────────────────────────────────────────────────

interface DetailPanelProps {
  segment: MarketSignalSegment
  persona: PersonaType
  onClose: () => void
}

function DetailPanel({ segment, persona, onClose }: DetailPanelProps) {
  const actionText = ACTION_TEXT[segment.signal][persona]

  return (
    <div className="mt-4 rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden animate-in slide-in-from-bottom-2 duration-200">
      {/* 패널 헤더 */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: SIGNAL_COLOR[segment.signal] }}
          />
          <span className="font-semibold text-gray-900">{segment.name}</span>
          <span className="text-xs text-gray-500">상세 분석</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          aria-label="닫기"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="px-5 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 좌측: 수치 정보 */}
          <div>
            {/* 핵심 수치 */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">S/D Ratio</p>
                <p
                  className="text-2xl font-bold"
                  style={{ color: SIGNAL_COLOR[segment.signal] }}
                >
                  {segment.ratio.toFixed(2)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">채용 수요</p>
                <p className="text-2xl font-bold text-gray-900">
                  {segment.demand.toLocaleString()}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">인재 공급</p>
                <p className="text-2xl font-bold text-gray-900">
                  {segment.supply.toLocaleString()}
                </p>
              </div>
            </div>

            {/* 4주 추세 */}
            <div className="flex items-center gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
              <TrendIcon trend={segment.trend4w} />
              <span className="text-sm text-gray-700">
                4주 추세:{' '}
                {segment.trend4w === 'UP' ? '상승 중' : segment.trend4w === 'DOWN' ? '하락 중' : '보합'}
              </span>
            </div>

            {/* 페르소나별 Action Text */}
            <div
              className="rounded-lg p-4 border"
              style={{
                backgroundColor: SIGNAL_COLOR[segment.signal] + '10',
                borderColor: SIGNAL_COLOR[segment.signal] + '40',
              }}
            >
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                {PERSONA_OPTIONS.find(p => p.value === persona)?.label} 추천 액션
              </p>
              <p className="text-sm text-gray-800 leading-relaxed">{actionText}</p>
            </div>
          </div>

          {/* 우측: 12주 스파크라인 */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
              12주 S/D Ratio 추이
            </p>
            <SparklineChart history={segment.weeklyHistory} />
            <div className="flex items-center gap-4 mt-2 justify-end">
              <span className="flex items-center gap-1 text-xs text-yellow-600">
                <span className="w-4 h-0.5 inline-block bg-yellow-400" /> 0.5 경계
              </span>
              <span className="flex items-center gap-1 text-xs text-green-600">
                <span className="w-4 h-0.5 inline-block bg-green-400" /> 1.0 경계
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── 메인 뷰 ───────────────────────────────────────────────────────────────────

export function MarketSignalsView() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [persona, setPersona] = useState<PersonaType>('INHOUSE_HR')

  const selectedSegment = MARKET_SIGNALS.find(s => s.id === selectedId) ?? null

  // 요약 지표 계산
  const redCount = MARKET_SIGNALS.filter(s => s.signal === 'RED').length
  const yellowCount = MARKET_SIGNALS.filter(s => s.signal === 'YELLOW').length
  const greenCount = MARKET_SIGNALS.filter(s => s.signal === 'GREEN').length
  const avgRatio = MARKET_SIGNALS.reduce((a, s) => a + s.ratio, 0) / MARKET_SIGNALS.length
  const mostCritical = [...MARKET_SIGNALS].sort((a, b) => a.ratio - b.ratio)[0] as typeof MARKET_SIGNALS[number] | undefined

  const handleCardClick = (id: string) => {
    // 같은 카드 재클릭 시 패널 닫기
    setSelectedId(prev => (prev === id ? null : id))
  }

  return (
    <div className="p-6">
      {/* 요약 메트릭 카드 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <MetricCard
          label="공급 희소 (RED)"
          value={redCount}
          sub={`전체 ${MARKET_SIGNALS.length}개 세그먼트 중`}
        />
        <MetricCard
          label="균형 (YELLOW)"
          value={yellowCount}
          sub="0.5 ≤ ratio < 1.0"
        />
        <MetricCard
          label="공급 우위 (GREEN)"
          value={greenCount}
          sub="ratio ≥ 1.0"
        />
        <MetricCard
          label="최고 긴급 세그먼트"
          value={mostCritical?.name ?? '-'}
          sub={mostCritical ? `ratio ${mostCritical.ratio.toFixed(2)} — 즉시 대응 필요` : '데이터 없음'}
        />
      </div>

      {/* 페르소나 선택 탭 */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-gray-500">
          평균 S/D Ratio: <span className="font-semibold text-gray-800">{avgRatio.toFixed(2)}</span>
          {' '}— 카드를 클릭하면 상세 패널이 표시됩니다.
        </p>
        <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
          {PERSONA_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setPersona(opt.value)}
              className={[
                'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                persona === opt.value
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700',
              ].join(' ')}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* 14개 세그먼트 카드 그리드 (3~4열) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
        {MARKET_SIGNALS.map(seg => (
          <SegmentCard
            key={seg.id}
            segment={seg}
            isSelected={selectedId === seg.id}
            onClick={() => handleCardClick(seg.id)}
          />
        ))}
      </div>

      {/* 상세 패널 — 선택된 세그먼트가 있을 때만 렌더 */}
      {selectedSegment && (
        <DetailPanel
          segment={selectedSegment}
          persona={persona}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}
