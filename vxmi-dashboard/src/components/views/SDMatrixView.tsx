import { useState, useMemo } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { SEGMENTS, enrichSegments } from '../../data/segments'
import { INDUSTRY_SEGMENTS, enrichIndustrySegments } from '../../data/industries'
import { MetricCard } from '../common/MetricCard'
import { DrilldownPanel } from '../common/DrilldownPanel'
import { SDDataTable } from '../common/SDDataTable'
import type { DrilldownItem } from '../../types'

type ViewMode = 'segment' | 'industry'

export function SDMatrixView() {
  const [viewMode, setViewMode] = useState<ViewMode>('segment')
  const enrichedSegments = useMemo(() => enrichSegments(SEGMENTS), [])
  const enrichedIndustry = useMemo(() => enrichIndustrySegments(INDUSTRY_SEGMENTS), [])
  const activeData = viewMode === 'segment' ? enrichedSegments : enrichedIndustry

  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null)
  const [hoveredSegmentId, setHoveredSegmentId] = useState<string | null>(null)
  const [drillSegment, setDrillSegment] = useState<string | null>(null)
  const [drillItems, setDrillItems] = useState<DrilldownItem[]>([])

  const activeSegmentId = hoveredSegmentId ?? selectedSegmentId

  const sdRatioMin = useMemo(() => {
    return activeData.reduce((acc, s) =>
      s.demand / s.supply < acc.ratio
        ? { name: s.name, ratio: s.demand / s.supply }
        : acc,
      { name: '', ratio: Infinity }
    )
  }, [activeData])

  const opportunityCount = activeData.filter(
    (s) => s.demand / s.supply <= 0.2
  ).length

  const bubbleData = useMemo(() => activeData.map((s) => ({
    name: s.name,
    x: s.demand,
    y: s.supply,
    z: s.otwPct * 3,
    color: s.color,
    sdRatio: (s.demand / s.supply).toFixed(2),
    otwPct: s.otwPct,
    segment: s,
  })), [activeData])

  const xMax = useMemo(() => {
    const max = Math.max(...activeData.map((s) => s.demand))
    return Math.ceil(max / 500) * 500 + 500
  }, [activeData])

  const yMax = useMemo(() => {
    const max = Math.max(...activeData.map((s) => s.supply))
    return Math.ceil(max / 2000) * 2000 + 2000
  }, [activeData])

  const handleBubbleClick = (data: any) => {
    if (!data?.segment) return
    const seg = data.segment
    setSelectedSegmentId(seg.id)
    setDrillSegment(seg.name)
    setDrillItems([
      { company: '— ', position: '드릴다운 데이터 (백엔드 연동 예정)', count: 0 },
    ])
  }

  const handleRowSelect = (segmentId: string, segmentName: string) => {
    setSelectedSegmentId(segmentId)
    setDrillSegment(segmentName)
    setDrillItems([
      { company: '— ', position: '드릴다운 데이터 (백엔드 연동 예정)', count: 0 },
    ])
  }

  const handleRowHover = (segmentId: string | null) => {
    setHoveredSegmentId(segmentId)
  }

  const switchMode = (mode: ViewMode) => {
    setViewMode(mode)
    setSelectedSegmentId(null)
    setHoveredSegmentId(null)
    setDrillSegment(null)
    setDrillItems([])
  }

  return (
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
            activeData.reduce((a, s) => a + s.demand / s.supply, 0) /
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
              key={seg.id}
              name={seg.name}
              data={[bubbleData.find((b) => b.segment.id === seg.id)!]}
              fill={seg.color}
              fillOpacity={
                activeSegmentId === seg.id
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
        segments={activeData}
        selectedSegmentId={selectedSegmentId}
        onRowSelect={handleRowSelect}
        onRowHover={handleRowHover}
        nameColumnLabel={viewMode === 'segment' ? '세그먼트' : '산업'}
      />

      <DrilldownPanel
        segmentName={drillSegment}
        items={drillItems}
        onClose={() => {
          setDrillSegment(null)
          setDrillItems([])
          setSelectedSegmentId(null)
        }}
      />
    </div>
  )
}
