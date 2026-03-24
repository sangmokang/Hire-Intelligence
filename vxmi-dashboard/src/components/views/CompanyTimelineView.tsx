import { useState, useMemo } from 'react'
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useCompanyTimeline } from '../../hooks/useDashboard'
import { useDashboardStore } from '../../stores/dashboardStore'
import { SEG_COLORS, SEG_OPTIONS, SUGGESTED_KEYWORDS } from '../../data/segments'
import { MetricCard } from '../common/MetricCard'
import { InlineSparkBar } from '../common/InlineSparkBar'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton, ChartSkeleton, TableSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'
import type { CompanyTimeline } from '../../types/dashboard'
import type { TimelineMode, TimelineWeeks, TimelineTopN, KeywordOperator } from '../../types'

const LINE_COLORS = ['#378ADD', '#1D9E75', '#D4537E', '#BA7517', '#7F77DD']

// Adapt CompanyTimeline to the display shape the UI uses
interface DisplayRankItem {
  rank: number
  company: string
  segment: string
  totalCount: number
  weeklySeries: number[]
  wowChange: number
  matchedKeywords?: string[]
}

function adaptTimelineData(timelines: CompanyTimeline[]): DisplayRankItem[] {
  return timelines.map((t, i) => {
    const weeklySeries = t.data.map(d => d.count)
    const totalCount = weeklySeries.reduce((a, b) => a + b, 0)
    const last = weeklySeries[weeklySeries.length - 1] ?? 0
    const prev = weeklySeries[weeklySeries.length - 2] ?? last
    const wowChange = prev > 0 ? ((last - prev) / prev) * 100 : 0
    return {
      rank: i + 1,
      company: t.company,
      segment: '',
      totalCount,
      weeklySeries,
      wowChange,
    }
  })
}

export function CompanyTimelineView() {
  const { filters } = useDashboardStore()
  const [mode, setMode] = useState<TimelineMode>('total')
  const [weeks, setWeeks] = useState<TimelineWeeks>(12)
  const [topN, setTopN] = useState<TimelineTopN>(20)
  const [segmentId, setSegmentId] = useState<string>('')
  const [keywords, setKeywords] = useState<string[]>([])
  const [keywordInput, setKeywordInput] = useState('')
  const [operator, setOperator] = useState<KeywordOperator>('AND')
  const [chartTopN, setChartTopN] = useState(5)
  const [trendKeyword, setTrendKeyword] = useState('')

  const timelineParams = useMemo(() => ({
    mode,
    weeks,
    topN,
    segments: segmentId ? [segmentId] : undefined,
    companyIds: undefined,
  }), [mode, weeks, topN, segmentId])

  const { data: response, isLoading, error } = useCompanyTimeline(timelineParams)

  const rankData: DisplayRankItem[] = useMemo(() => {
    if (!response?.data) return []
    return adaptTimelineData(response.data)
  }, [response])

  const top5 = rankData.slice(0, chartTopN)
  const restData = rankData.slice(chartTopN)

  const weeksCount = rankData[0]?.weeklySeries.length ?? weeks
  const weekLabels = useMemo(() => {
    if (rankData[0]?.weeklySeries) {
      // Use week labels from API data if available
      const apiWeeks = response?.data?.[0]?.data?.map(d => d.week) ?? []
      if (apiWeeks.length > 0) return apiWeeks
    }
    return Array.from({ length: weeksCount }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() - (weeksCount - 1 - i) * 7)
      return `${d.getMonth() + 1}/${d.getDate()}`
    })
  }, [rankData, weeksCount, response])

  const chartData = useMemo(() => weekLabels.map((label, wi) => {
    const point: Record<string, any> = { week: label }
    top5.forEach((r) => { point[r.company] = r.weeklySeries[wi] ?? 0 })
    if (restData.length > 0) {
      point['기타'] = restData.reduce((sum, r) => sum + (r.weeklySeries[wi] ?? 0), 0)
    }
    return point
  }), [weekLabels, top5, restData])

  const addKeyword = () => {
    const kw = keywordInput.trim()
    if (!kw || keywords.includes(kw) || keywords.length >= 5) return
    setKeywords([...keywords, kw])
    setKeywordInput('')
  }

  const removeKeyword = (kw: string) => setKeywords(keywords.filter((k) => k !== kw))

  if (isLoading) {
    return (
      <div>
        <div className="grid grid-cols-4 gap-3 mb-5">
          {[0,1,2,3].map((i) => <CardSkeleton key={i} />)}
        </div>
        <ChartSkeleton height={260} />
        <div className="mt-4"><TableSkeleton rows={5} /></div>
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

  if (rankData.length === 0) {
    return <EmptyState title="타임라인 데이터가 없습니다" description="선택한 조건에 맞는 기업 타임라인 데이터가 없습니다." />
  }

  return (
    <ErrorBoundary>
      <div>
        {/* Summary Metrics */}
        <div className="grid grid-cols-4 gap-3 mb-5">
          <MetricCard label="조회 기업 수" value={rankData.length.toLocaleString()} sub={`Top ${topN} 기준`} />
          <MetricCard
            label="최다 채용 기업"
            value={rankData[0]?.company ?? '—'}
            sub={`${rankData[0]?.totalCount.toLocaleString() ?? 0}건`}
          />
          <MetricCard
            label="가장 빠르게 성장"
            value={[...rankData].sort((a, b) => b.wowChange - a.wowChange)[0]?.company ?? '—'}
            sub={`+${[...rankData].sort((a, b) => b.wowChange - a.wowChange)[0]?.wowChange.toFixed(1) ?? 0}% WoW`}
          />
          <MetricCard
            label={mode === 'compound' ? '매칭 키워드' : trendKeyword ? '키워드 트렌드' : '조회 기간'}
            value={mode === 'compound' ? `${keywords.length}개` : trendKeyword ? `"${trendKeyword}"` : `${weeks}주`}
            sub={mode === 'compound' ? `${operator} 조건` : trendKeyword ? `${weeks}주 기준` : '롤링 윈도우'}
          />
        </div>

        {/* Mode Tabs */}
        <div className="flex gap-2 mb-4">
          {([
            { id: 'total' as const, label: '총 채용 규모' },
            { id: 'keyword' as const, label: '단일 키워드' },
            { id: 'compound' as const, label: '복합 키워드' },
          ]).map((m) => (
            <button
              key={m.id}
              onClick={() => { setMode(m.id); setKeywords([]); setTrendKeyword('') }}
              className={`px-4 py-2 text-xs rounded-lg border transition-colors ${
                mode === m.id
                  ? 'bg-gray-900 text-white border-transparent font-medium'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-xl border border-gray-200">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">기간</span>
            <select
              value={weeks}
              onChange={(e) => setWeeks(Number(e.target.value) as TimelineWeeks)}
              className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900"
            >
              {([4, 8, 12, 26, 52] as const).map((w) => (
                <option key={w} value={w}>{w}주</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">키워드</span>
            <div className="relative">
              <input
                type="text"
                value={trendKeyword}
                onChange={(e) => setTrendKeyword(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur() }}
                placeholder="키워드 검색 (예: Python, React)"
                className="text-xs pl-2 pr-7 py-1.5 w-48 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:border-gray-400"
              />
              {trendKeyword && (
                <button
                  onClick={() => setTrendKeyword('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
                >
                  ×
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Top</span>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value) as TimelineTopN)}
              className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900"
            >
              {([20, 50, 100] as const).map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">세그먼트</span>
            <select
              value={segmentId}
              onChange={(e) => setSegmentId(e.target.value === '전체' ? '' : e.target.value)}
              className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900"
            >
              {SEG_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* Keyword Input — Mode B/C */}
        {(mode === 'keyword' || mode === 'compound') && (
          <div className="mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
            <div className="flex gap-2 mb-3">
              <input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') addKeyword() }}
                placeholder={mode === 'keyword' ? '키워드 입력 (예: Python)' : `키워드 추가 (최대 5개, 현재 ${keywords.length}/5)`}
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:border-gray-400"
                disabled={mode === 'keyword' && keywords.length >= 1}
              />
              <button
                onClick={addKeyword}
                disabled={(mode === 'keyword' && keywords.length >= 1) || keywords.length >= 5}
                className="px-4 py-2 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-40"
              >
                추가
              </button>
            </div>

            {keywords.length === 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3">
                <span className="text-xs text-gray-500 self-center">추천:</span>
                {SUGGESTED_KEYWORDS.slice(0, 8).map((kw) => (
                  <button
                    key={kw}
                    onClick={() => { setKeywords([...keywords, kw]) }}
                    className="text-xs px-2 py-0.5 border border-gray-200 rounded-md text-gray-500 hover:bg-gray-100 transition-colors"
                  >
                    {kw}
                  </button>
                ))}
              </div>
            )}

            {keywords.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                {keywords.map((kw) => (
                  <span
                    key={kw}
                    className="flex items-center gap-1 text-xs px-2.5 py-1 bg-white border border-gray-200 rounded-md text-gray-900"
                  >
                    {kw}
                    <button
                      onClick={() => removeKeyword(kw)}
                      className="text-gray-400 hover:text-gray-900 ml-0.5"
                    >
                      ×
                    </button>
                  </span>
                ))}

                {mode === 'compound' && keywords.length > 1 && (
                  <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200">
                    <span className="text-xs text-gray-500">연산자:</span>
                    {(['AND', 'OR'] as const).map((op) => (
                      <button
                        key={op}
                        onClick={() => setOperator(op)}
                        className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
                          operator === op
                            ? 'bg-gray-900 text-white border-transparent font-medium'
                            : 'border-gray-200 text-gray-500 hover:bg-gray-100'
                        }`}
                      >
                        {op}
                      </button>
                    ))}
                    <span className="text-xs text-gray-500">
                      {operator === 'AND' ? '모두 채용 중인 기업' : '하나 이상 채용 중인 기업'}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Time-series Line Chart */}
        <div className="mb-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">{trendKeyword ? `"${trendKeyword}" 키워드 트렌드` : '상위 기업 시계열 추이'}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">차트 표시:</span>
              {[3, 5, 10].map((n) => (
                <button
                  key={n}
                  onClick={() => setChartTopN(n)}
                  className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                    chartTopN === n
                      ? 'bg-gray-900 text-white border-transparent'
                      : 'border-gray-200 text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  Top {n}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 8, right: 20, bottom: 8, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.08)" />
              <XAxis dataKey="week" tick={{ fontSize: 10 }} />
              <YAxis tickFormatter={(v: number) => v.toLocaleString()} tick={{ fontSize: 10 }} width={45} />
              <Tooltip
                formatter={(value: any, name: any) => [Number(value).toLocaleString(), name]}
                labelFormatter={(l: any) => `${l}주차`}
              />
              {top5.map((r, i) => (
                <Line
                  key={r.company}
                  type="monotone"
                  dataKey={r.company}
                  stroke={LINE_COLORS[i] ?? '#888780'}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              ))}
              {restData.length > 0 && (
                <Line
                  type="monotone"
                  dataKey="기타"
                  stroke="#C4C3BB"
                  strokeWidth={1.5}
                  strokeDasharray="4 3"
                  dot={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2">
            {top5.map((r, i) => (
              <span key={r.company} className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className="w-3 h-0.5 inline-block" style={{ background: LINE_COLORS[i] }} />
                {r.company}
              </span>
            ))}
            {restData.length > 0 && (
              <span className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className="w-3 h-0.5 inline-block" style={{ background: '#C4C3BB' }} />
                기타 {restData.length}개 기업 합산
              </span>
            )}
          </div>
        </div>

        {/* Ranking Table */}
        <div className="flex flex-col gap-1.5">
          <div className="grid gap-2 px-4 py-2 text-xs text-gray-500"
            style={{ gridTemplateColumns: '28px 1fr 90px 88px 72px 64px' }}
          >
            <span>#</span>
            <span>기업</span>
            <span>세그먼트</span>
            <span>12주 추이</span>
            <span className="text-right">총 공고</span>
            <span className="text-right">전주比</span>
          </div>

          {rankData.map((item, i) => {
            const segColor = SEG_COLORS[item.segment] ?? { bg: '#F1EFE8', text: '#5F5E5A' }
            return (
              <div
                key={item.company}
                className="grid gap-2 items-center px-4 py-2.5 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors text-sm"
                style={{ gridTemplateColumns: '28px 1fr 90px 88px 72px 64px' }}
              >
                <span className="text-xs font-medium text-gray-500">{item.rank}</span>
                <div>
                  <span className="font-medium text-sm text-gray-900">{item.company}</span>
                  {mode === 'compound' && item.matchedKeywords && (
                    <div className="flex gap-1 mt-0.5">
                      {item.matchedKeywords.map((kw) => (
                        <span key={kw} className="text-xs px-1.5 py-0 bg-white border border-gray-200 rounded text-gray-500">
                          {kw} ✓
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span
                  className="text-xs px-2 py-0.5 rounded text-center"
                  style={{ background: segColor.bg, color: segColor.text }}
                >
                  {item.segment || '—'}
                </span>
                <InlineSparkBar data={item.weeklySeries} color={LINE_COLORS[i] ?? '#888780'} />
                <span className="text-sm font-medium text-right text-gray-900">
                  {item.totalCount.toLocaleString()}
                </span>
                <span
                  className={`text-xs text-right font-medium ${
                    item.wowChange > 0 ? 'text-green-600' :
                    item.wowChange < 0 ? 'text-red-500' :
                    'text-gray-500'
                  }`}
                >
                  {item.wowChange > 0 ? '▲' : item.wowChange < 0 ? '▼' : '—'}
                  {Math.abs(item.wowChange).toFixed(1)}%
                </span>
              </div>
            )
          })}
        </div>

        {/* 영업 인텔리전스 힌트 */}
        <div className="mt-5 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-500">
            <span className="font-medium text-gray-900">영업 활용:</span>{' '}
            {mode === 'total' && !trendKeyword && '12주 이상 꾸준히 상위 기업 = 지속 채용 중 → 서치 의뢰 가능성 높음'}
            {mode === 'total' && trendKeyword && `"${trendKeyword}" 키워드를 포함한 채용 공고 트렌드 — 해당 스킬 수요 증가 기업을 타겟으로 후보자 제안 가능`}
            {mode === 'keyword' && `"${keywords[0] ?? '키워드'}" 공고 급증 기업 = 해당 스킬 후보자 배치 타겟`}
            {mode === 'compound' && `${operator} 조건 매칭 기업 = 해당 복합 스킬셋 보유 후보자 즉시 제안 가능`}
          </p>
        </div>
      </div>
    </ErrorBoundary>
  )
}
