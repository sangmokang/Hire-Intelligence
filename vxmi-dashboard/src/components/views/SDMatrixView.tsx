import { useState, useMemo } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useSDMatrix, useSDMatrixDrilldown } from '../../hooks/useDashboard'
import { MetricCard } from '../common/MetricCard'
import { DrilldownPanel } from '../common/DrilldownPanel'
import { SDDataTable } from '../common/SDDataTable'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { ChartSkeleton, CardSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'
import type { SDMatrixItem } from '../../types/dashboard'

type ViewMode = 'segment' | 'industry'

// Color palette assigned by index since API type has no color field
const SEGMENT_COLORS = [
  '#378ADD', '#1D9E75', '#E24B4A', '#D4537E', '#888780',
  '#BA7517', '#7F77DD', '#5DCAA5', '#F0997B', '#D85A30',
  '#97C459', '#FAC775', '#93B1EB', '#ED93B1',
]

interface EnrichedSDItem extends SDMatrixItem {
  color: string
}

function enrichWithColor(items: SDMatrixItem[]): EnrichedSDItem[] {
  return items.map((item, i) => ({
    ...item,
    color: SEGMENT_COLORS[i % SEGMENT_COLORS.length],
  }))
}

// Adapter: convert SDMatrixItem to the shape SDDataTable expects (id, name, demand, supply, otwPct, color + extras)
function toTableSegment(item: EnrichedSDItem) {
  return {
    id: item.segmentId,
    name: item.segmentName,
    demand: item.demand,
    supply: item.supply,
    otwPct: item.otwPct,
    color: item.color,
    sdRatio: item.sdRatio,
    quadrant: item.quadrant,
    demandWoW: 0,
    supplyWoW: 0,
    topCompanies: [] as string[],
  }
}

export function SDMatrixView() {
  const [viewMode, setViewMode] = useState<ViewMode>('segment')
  const { data: response, isLoading, error } = useSDMatrix(undefined, viewMode)

  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null)
  const [hoveredSegmentId, setHoveredSegmentId] = useState<string | null>(null)
  const [drillSegment, setDrillSegment] = useState<string | null>(null)

  const { data: drilldownResponse, isLoading: drilldownLoading } = useSDMatrixDrilldown(selectedSegmentId)

  const activeSegmentId = hoveredSegmentId ?? selectedSegmentId

  const activeData: EnrichedSDItem[] = useMemo(() => {
    if (!response?.data) return []
    // MSW/백엔드 응답: { summary, segments } 또는 직접 배열
    const items = Array.isArray(response.data) ? response.data : (response.data as Record<string, unknown>).segments as SDMatrixItem[] | undefined;
    return items ? enrichWithColor(items) : []
  }, [response])

  const tableSegments = useMemo(() => activeData.map(toTableSegment), [activeData])

  const sdRatioMin = useMemo(() => {
    if (activeData.length === 0) return { name: '—', ratio: 0 }
    return activeData.reduce((acc, s) =>
      s.sdRatio < acc.ratio
        ? { name: s.segmentName, ratio: s.sdRatio }
        : acc,
      { name: activeData[0].segmentName, ratio: activeData[0].sdRatio }
    )
  }, [activeData])

  const opportunityCount = activeData.filter((s) => s.sdRatio <= 0.2).length

  const bubbleData = useMemo(() => activeData.map((s) => ({
    name: s.segmentName,
    x: s.demand,
    y: s.supply,
    z: s.otwPct * 3,
    color: s.color,
    sdRatio: s.sdRatio.toFixed(2),
    otwPct: s.otwPct,
    segment: s,
  })), [activeData])

  const xMax = useMemo(() => {
    if (activeData.length === 0) return 1000
    const max = Math.max(...activeData.map((s) => s.demand))
    return Math.ceil(max / 500) * 500 + 500
  }, [activeData])

  const yMax = useMemo(() => {
    if (activeData.length === 0) return 5000
    const max = Math.max(...activeData.map((s) => s.supply))
    return Math.ceil(max / 2000) * 2000 + 2000
  }, [activeData])

  const handleBubbleClick = (data: { segment?: EnrichedSDItem } | null) => {
    if (!data?.segment) return
    const seg = data.segment
    setSelectedSegmentId(seg.segmentId)
    setDrillSegment(seg.segmentName)
  }

  const handleRowSelect = (segmentId: string, segmentName: string) => {
    setSelectedSegmentId(segmentId)
    setDrillSegment(segmentName)
  }

  const handleRowHover = (segmentId: string | null) => {
    setHoveredSegmentId(segmentId)
  }

  const switchMode = (mode: ViewMode) => {
    setViewMode(mode)
    setSelectedSegmentId(null)
    setHoveredSegmentId(null)
    setDrillSegment(null)
  }

  if (isLoading) {
    return (
      <div>
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[0,1,2,3].map((i) => <CardSkeleton key={i} />)}
        </div>
        <ChartSkeleton height={420} />
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

  if (activeData.length === 0) {
    return <EmptyState title="S/D 매트릭스 데이터가 없습니다" description="수집된 세그먼트 데이터가 없습니다." />
  }

  return (
    <ErrorBoundary>
      <div>
        <div className="grid grid-cols-4 gap-3 mb-6">
          <MetricCard
            label="전체 채용 공고"
            value={activeData.reduce((a, s) => a + s.demand, 0).toLocaleString()}
            sub={viewMode === 'segment' ? `${activeData.length}개 세그먼트` : `${activeData.length}개 산업`}
          />
          <MetricCard
            label={viewMode === 'segment' ? '기회지대 세그먼트' : '기회지대 산업'}
            value={opportunityCount}
            sub="수요공급 ratio ≤ 0.20"
          />
          <MetricCard
            label="평균 수요공급 Ratio"
            value={(
              activeData.reduce((a, s) => a + s.sdRatio, 0) /
              activeData.length
            ).toFixed(2)}
            sub="전주 대비 집계 필요"
          />
          <MetricCard
            label="최고 기회"
            value={sdRatioMin.name}
            sub={`ratio ${sdRatioMin.ratio.toFixed(2)}`}
          />
        </div>

        <div className="flex items-center justify-end mb-4">
          <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
            <button
              onClick={() => switchMode('segment')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'segment'
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              세그먼트별
            </button>
            <button
              onClick={() => switchMode('industry')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'industry'
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              산업별
            </button>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={420}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
            <XAxis
              type="number"
              dataKey="x"
              name="수요"
              tickFormatter={(v: number) => v.toLocaleString()}
              label={{ value: '채용 수요 (공고 수)', position: 'insideBottom', offset: -10, fontSize: 11 }}
              domain={[0, xMax]}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="공급"
              tickFormatter={(v: number) => v.toLocaleString()}
              label={{ value: '인재 공급', angle: -90, position: 'insideLeft', fontSize: 11 }}
              domain={[0, yMax]}
            />
            <ZAxis type="number" dataKey="z" range={[60, 400]} />
            <Tooltip
              content={({ payload }) => {
                if (!payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="bg-white border border-gray-200 rounded-lg p-3 text-xs shadow-sm">
                    <p className="font-medium mb-1 text-gray-900">{d.name}</p>
                    <p className="text-gray-500">수요: {d.x.toLocaleString()}</p>
                    <p className="text-gray-500">공급: {d.y.toLocaleString()}</p>
                    <p className="text-gray-500">OTW: {d.otwPct}%</p>
                    <p className="font-medium mt-1 text-gray-900">수요공급 ratio: {d.sdRatio}</p>
                  </div>
                )
              }}
            />
            {activeData.map((seg) => (
              <Scatter
                key={seg.segmentId}
                name={seg.segmentName}
                data={[bubbleData.find((b) => b.segment.segmentId === seg.segmentId)!]}
                fill={seg.color}
                fillOpacity={
                  activeSegmentId === seg.segmentId
                    ? 1.0
                    : activeSegmentId
                      ? 0.3
                      : 0.75
                }
                onClick={handleBubbleClick}
                style={{ cursor: 'pointer' }}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>

        {/* Toggle buttons below chart */}
        <div className="flex items-center justify-start mt-4 mb-2">
          <div className="inline-flex rounded-lg border border-gray-200 bg-white p-0.5">
            <button
              onClick={() => switchMode('segment')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'segment'
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              세그먼트별
            </button>
            <button
              onClick={() => switchMode('industry')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'industry'
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              기업별
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-400 mb-4 flex items-center justify-center gap-1">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
            <path d="M13 13l6 6" />
          </svg>
          타일을 클릭하여 상세 데이터를 확인하세요
        </p>

        <SDDataTable
          segments={tableSegments}
          selectedSegmentId={selectedSegmentId}
          onRowSelect={handleRowSelect}
          onRowHover={handleRowHover}
          nameColumnLabel={viewMode === 'segment' ? '세그먼트' : '산업'}
        />

        <DrilldownPanel
          segmentId={selectedSegmentId}
          segmentName={drillSegment}
          drilldown={drilldownResponse?.data}
          isLoading={drilldownLoading}
          onClose={() => {
            setDrillSegment(null)
            setSelectedSegmentId(null)
          }}
        />
      </div>
    </ErrorBoundary>
  )
}
