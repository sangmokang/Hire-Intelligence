import { useState } from 'react'
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { TREND_WEEKS, TREND_SERIES } from '../../data/trends'
import { SEGMENTS } from '../../data/segments'
import { searchByKeyword } from '../../data/keywordMap'
import { MetricCard } from '../common/MetricCard'

export function HiringTrendsView() {
  const [hiddenSegs, setHiddenSegs] = useState<Set<string>>(new Set())
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0])
  const [keyword, setKeyword] = useState('')
  const [activeKeyword, setActiveKeyword] = useState('')
  const [matchedSegmentIds, setMatchedSegmentIds] = useState<string[]>([])

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
    // Filter to only IDs that exist in TREND_SERIES
    const trendIds = new Set(TREND_SERIES.map((s) => s.id))
    const filtered = matched.filter((id) => trendIds.has(id))
    setMatchedSegmentIds(filtered)
    setActiveKeyword(keyword.trim())
    // Hide all segments not in matched list
    const newHidden = new Set(
      TREND_SERIES.map((s) => s.id).filter((id) => !filtered.includes(id))
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

  const visibleCount = TREND_SERIES.filter((s) => !hiddenSegs.has(s.id)).length

  const chartData = TREND_WEEKS.map((week, wi) => {
    const point: Record<string, any> = { week }
    TREND_SERIES.forEach((s) => { point[s.id] = s.data[wi] })
    return point
  })

  const dateFilterActive = fromDate || toDate

  return (
    <div>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <MetricCard label="조회 기간" value="12주" sub="2024.10 — 12" />
        <MetricCard label="최고 성장 직군" value="Data/AI" sub="+34% MoM" />
        <MetricCard label="최다 공고 주차" value="12/2" sub="SW엔지니어링 피크" />
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
              const series = TREND_SERIES.find((s) => s.id === id)
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
        {TREND_SERIES.map((s) => (
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
              TREND_SERIES.find((s) => s.id === name)?.name ?? name,
            ]}
          />
          {TREND_SERIES.map((s) => (
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
  )
}
