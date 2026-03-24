import { useState, useMemo } from 'react'
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useHiringTrends } from '../../hooks/useDashboard'
import { SEGMENTS } from '../../data/segments'
import { searchByKeyword } from '../../data/keywordMap'
import { MetricCard } from '../common/MetricCard'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton, ChartSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'

const TREND_COLORS = [
  '#378ADD', '#1D9E75', '#E24B4A', '#D4537E', '#888780',
  '#BA7517', '#7F77DD', '#5DCAA5', '#F0997B', '#D85A30',
  '#97C459', '#FAC775', '#93B1EB', '#ED93B1',
]

const DEFAULT_SEGMENTS = SEGMENTS.map(s => s.id)

export function HiringTrendsView() {
  const [hiddenSegs, setHiddenSegs] = useState<Set<string>>(new Set())
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0])
  const [keyword, setKeyword] = useState('')
  const [activeKeyword, setActiveKeyword] = useState('')
  const [matchedSegmentIds, setMatchedSegmentIds] = useState<string[]>([])

  const { data: response, isLoading, error } = useHiringTrends(12, DEFAULT_SEGMENTS)

  const trendSeries = useMemo(() => {
    if (!response?.data) return []
    return response.data.map((s, i) => ({
      id: s.segmentId,
      name: s.segmentName,
      color: TREND_COLORS[i % TREND_COLORS.length],
      data: s.data.map(d => d.count),
      weeks: s.data.map(d => d.week),
    }))
  }, [response])

  const trendWeeks = useMemo(() => {
    if (trendSeries.length === 0) return []
    return trendSeries[0].weeks
  }, [trendSeries])

  const toggleSeg = (id: string) => {
    setHiddenSegs((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleSearch = () => {
    const trimmed = keyword.trim()
    if (!trimmed) {
      setActiveKeyword('')
      setMatchedSegmentIds([])
      setHiddenSegs(new Set())
      return
    }
    const matched = searchByKeyword(trimmed)
    // Filter to only IDs that exist in trendSeries
    const trendIds = new Set(trendSeries.map((s) => s.id))
    const filtered = matched.filter((id) => trendIds.has(id))
    setMatchedSegmentIds(filtered)
    setActiveKeyword(keyword.trim())
    // Hide all segments not in matched list
    const newHidden = new Set(
      trendSeries.map((s) => s.id).filter((id) => !filtered.includes(id))
    )
    setHiddenSegs(newHidden)
  }

  const handleClear = () => {
    setFromDate('')
    setToDate('')
    setKeyword('')
    setActiveKeyword('')
    setMatchedSegmentIds([])
    setHiddenSegs(new Set())
  }

  const visibleCount = trendSeries.filter((s) => !hiddenSegs.has(s.id)).length

  const chartData = useMemo(() => trendWeeks.map((week, wi) => {
    const point: Record<string, any> = { week }
    trendSeries.forEach((s) => { point[s.id] = s.data[wi] })
    return point
  }), [trendWeeks, trendSeries])

  const dateFilterActive = fromDate || toDate

  // Compute summary metrics
  const growthSorted = useMemo(() => {
    if (trendSeries.length === 0) return []
    return [...trendSeries].sort((a, b) => {
      const aLast = a.data[a.data.length - 1] ?? 0
      const aFirst = a.data[0] ?? 1
      const bLast = b.data[b.data.length - 1] ?? 0
      const bFirst = b.data[0] ?? 1
      return (bLast / bFirst) - (aLast / aFirst)
    })
  }, [trendSeries])

  const peakWeek = useMemo(() => {
    if (trendSeries.length === 0 || trendWeeks.length === 0) return { week: '—', seg: '—' }
    let maxCount = 0
    let maxWeek = trendWeeks[0]
    let maxSeg = trendSeries[0]?.name ?? '—'
    trendSeries.forEach(s => {
      s.data.forEach((count, wi) => {
        if (count > maxCount) {
          maxCount = count
          maxWeek = trendWeeks[wi]
          maxSeg = s.name
        }
      })
    })
    return { week: maxWeek, seg: maxSeg }
  }, [trendSeries, trendWeeks])

  if (isLoading) {
    return (
      <div>
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[0,1,2,3].map((i) => <CardSkeleton key={i} />)}
        </div>
        <ChartSkeleton height={320} />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorBoundary>
        <div className="py-8 text-center text-sm text-red-500">
          데이터를 불러오는 중 오류가 발생했습니다: {(error as Error).message}
        </div>
      </ErrorBoundary>
    )
  }

  if (trendSeries.length === 0) {
    return <EmptyState title="트렌드 데이터가 없습니다" description="수집된 채용 트렌드 데이터가 없습니다." />
  }

  return (
    <ErrorBoundary>
      <div>
        <div className="grid grid-cols-4 gap-3 mb-6">
          <MetricCard label="조회 기간" value={`${trendWeeks.length}주`} sub={trendWeeks.length > 0 ? `${trendWeeks[0]} — ${trendWeeks[trendWeeks.length - 1]}` : ''} />
          <MetricCard
            label="최고 성장 직군"
            value={growthSorted[0]?.name ?? '—'}
            sub="기간 내 최대 성장"
          />
          <MetricCard label="최다 공고 주차" value={peakWeek.week} sub={`${peakWeek.seg} 피크`} />
          <MetricCard label="추적 직군" value={String(visibleCount)} sub="세그먼트" />
        </div>

        {/* Filter Bar */}
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-3 mb-4">
          <div className="flex flex-wrap items-end gap-3">
            {/* From date */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">From</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900"
              />
            </div>

            {/* To date */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">To</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900"
              />
            </div>

            <div className="w-px h-8 bg-gray-200 self-center" />

            {/* Keyword search */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">직군 키워드</label>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="예: 개발자, AI, 마케팅"
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 w-44"
              />
            </div>

            <button
              onClick={handleSearch}
              className="px-3 py-1.5 text-xs bg-gray-900 text-white rounded-md hover:bg-gray-800"
            >
              검색
            </button>

            {(activeKeyword || dateFilterActive) && (
              <button
                onClick={handleClear}
                className="px-3 py-1.5 text-xs border border-gray-200 rounded-md text-gray-500 hover:bg-gray-100"
              >
                초기화
              </button>
            )}
          </div>

          {/* Date filter notice */}
          {dateFilterActive && (
            <p className="mt-2 text-xs text-gray-400">
              * 기간 필터는 백엔드 연동 후 활성화됩니다
            </p>
          )}

          {/* Matched segment badges */}
          {activeKeyword && matchedSegmentIds.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              <span className="text-xs text-gray-500 self-center">
                &ldquo;{activeKeyword}&rdquo; 매칭:
              </span>
              {matchedSegmentIds.map((id) => {
                const series = trendSeries.find((s) => s.id === id)
                const seg = SEGMENTS.find((s) => s.id === id)
                const color = series?.color ?? seg?.color ?? '#888'
                const name = series?.name ?? seg?.name ?? id
                return (
                  <span
                    key={id}
                    className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs"
                    style={{ backgroundColor: color + '20', color }}
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    {name}
                  </span>
                )
              })}
            </div>
          )}

          {activeKeyword && matchedSegmentIds.length === 0 && (
            <p className="mt-2 text-xs text-gray-400">
              &ldquo;{activeKeyword}&rdquo;에 해당하는 직군을 찾을 수 없습니다.
            </p>
          )}
        </div>

        {/* Legend / Toggle */}
        <div className="flex flex-wrap gap-2 mb-4">
          {trendSeries.map((s) => (
            <button
              key={s.id}
              onClick={() => toggleSeg(s.id)}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs border border-gray-200 rounded-md transition-opacity ${
                hiddenSegs.has(s.id) ? 'opacity-40' : ''
              }`}
            >
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: s.color }}
              />
              {s.name}
            </button>
          ))}
        </div>

        {/* Line Chart */}
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
            <XAxis dataKey="week" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v: number) => v.toLocaleString()} tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value: any, name: any) => [
                Number(value).toLocaleString(),
                trendSeries.find((s) => s.id === name)?.name ?? name,
              ]}
            />
            {trendSeries.map((s) => (
              <Line
                key={s.id}
                type="monotone"
                dataKey={s.id}
                stroke={s.color}
                strokeWidth={2}
                dot={{ r: 4, fill: s.color, strokeWidth: 1.5, stroke: '#fff' }}
                activeDot={{ r: 7 }}
                hide={hiddenSegs.has(s.id)}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ErrorBoundary>
  )
}
