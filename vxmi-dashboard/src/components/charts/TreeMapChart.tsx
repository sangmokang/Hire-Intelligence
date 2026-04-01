import { useState, useMemo, useCallback } from 'react'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface TreeMapChartProps {
  data: Array<{
    company: string
    segment: string
    weeklyCount: number
    weekOverWeekChange: number
    positions: string[]
  }>
}

interface LayoutRect {
  x: number
  y: number
  w: number
  h: number
  name: string
  value: number
  percentage: number
  color: string
  /** For drill-down: which segment this item belongs to */
  segment?: string
}

interface TreeItem {
  name: string
  value: number
  color: string
  segment?: string
}

/* ------------------------------------------------------------------ */
/*  Color palette (muted pastels - Anthropic Economic Index aesthetic) */
/* ------------------------------------------------------------------ */

const SEGMENT_TREEMAP_COLORS: Record<string, string> = {
  'SW엔지니어링': '#8FBC94',
  '제조': '#D4B896',
  'Product': '#C9909A',
  'Data/AI': '#8BB0C4',
  '연구개발': '#A0A0C8',
  '운영': '#C4B8A8',
  '영업': '#D4948C',
  '마케팅': '#B098C8',
  '재무': '#88B8A0',
  'HR': '#D4A0B0',
  'UX/UI': '#D4A878',
  '법무': '#A8C498',
  '물류SCM': '#D4C888',
  '의료헬스케어': '#C890A8',
}

function getSegmentColor(segment: string): string {
  return SEGMENT_TREEMAP_COLORS[segment] ?? '#B0B0B0'
}

/* ------------------------------------------------------------------ */
/*  Squarified treemap algorithm                                       */
/* ------------------------------------------------------------------ */

const GAP = 3

/** Worst aspect ratio in a candidate row */
function worstRatio(row: number[], side: number): number {
  const s = row.reduce((a, b) => a + b, 0)
  if (s === 0) return Infinity
  const s2 = s * s
  const side2 = side * side
  let worst = 0
  for (const r of row) {
    if (r === 0) continue
    const ratio = Math.max((side2 * r) / s2, s2 / (side2 * r))
    if (ratio > worst) worst = ratio
  }
  return worst
}

function squarify(items: TreeItem[], bounds: { x: number; y: number; w: number; h: number }): LayoutRect[] {
  if (items.length === 0) return []

  const totalValue = items.reduce((s, it) => s + it.value, 0)
  if (totalValue === 0) return []

  // Normalise values to areas
  const totalArea = bounds.w * bounds.h
  const areas = items
    .map((it) => ({ ...it, area: (it.value / totalValue) * totalArea }))
    .sort((a, b) => b.area - a.area)

  const rects: LayoutRect[] = []
  let { x, y, w, h } = bounds

  let i = 0
  while (i < areas.length) {
    const shortSide = Math.min(w, h)
    const row: number[] = [areas[i].area]
    const rowItems = [areas[i]]
    let best = worstRatio(row, shortSide)
    i++

    while (i < areas.length) {
      const candidate = [...row, areas[i].area]
      const next = worstRatio(candidate, shortSide)
      if (next <= best) {
        row.push(areas[i].area)
        rowItems.push(areas[i])
        best = next
        i++
      } else {
        break
      }
    }

    // Lay out the row
    const rowSum = row.reduce((a, b) => a + b, 0)
    const rowThickness = shortSide === 0 ? 0 : rowSum / shortSide

    if (w >= h) {
      // Row fills left side vertically
      let cy = y
      for (let j = 0; j < row.length; j++) {
        const itemH = rowThickness === 0 ? 0 : row[j] / rowThickness
        rects.push({
          x: x,
          y: cy,
          w: rowThickness,
          h: itemH,
          name: rowItems[j].name,
          value: rowItems[j].value,
          percentage: totalValue === 0 ? 0 : (rowItems[j].value / totalValue) * 100,
          color: rowItems[j].color,
          segment: rowItems[j].segment,
        })
        cy += itemH
      }
      x += rowThickness
      w -= rowThickness
    } else {
      // Row fills top side horizontally
      let cx = x
      for (let j = 0; j < row.length; j++) {
        const itemW = rowThickness === 0 ? 0 : row[j] / rowThickness
        rects.push({
          x: cx,
          y: y,
          w: itemW,
          h: rowThickness,
          name: rowItems[j].name,
          value: rowItems[j].value,
          percentage: totalValue === 0 ? 0 : (rowItems[j].value / totalValue) * 100,
          color: rowItems[j].color,
          segment: rowItems[j].segment,
        })
        cx += itemW
      }
      y += rowThickness
      h -= rowThickness
    }
  }

  return rects
}

/* ------------------------------------------------------------------ */
/*  Label rendering helper                                             */
/* ------------------------------------------------------------------ */

function TileLabel({ rect, isCompany }: { rect: LayoutRect; isCompany: boolean }) {
  const showFull = rect.w > 120 && rect.h > 60
  const showName = rect.w > 80 && rect.h > 40

  if (!showName) return null

  const valueText = isCompany
    ? rect.value.toLocaleString()
    : `${rect.percentage.toFixed(1)}%`

  return (
    <div className="absolute inset-0 flex flex-col items-start justify-start p-3 pointer-events-none select-none overflow-hidden">
      <span
        className="font-semibold leading-tight max-w-full truncate"
        style={{
          fontSize: rect.w < 110 ? '12px' : '14px',
          color: 'rgba(0,0,0,0.8)',
        }}
      >
        {rect.name}
      </span>
      {showFull && (
        <span
          className="leading-tight mt-0.5"
          style={{
            fontSize: rect.w < 110 ? '11px' : '13px',
            color: 'rgba(0,0,0,0.55)',
          }}
        >
          {valueText}
        </span>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Tooltip                                                            */
/* ------------------------------------------------------------------ */

function TileTooltip({ rect, isCompany }: { rect: LayoutRect; isCompany: boolean }) {
  const showName = rect.w > 80 && rect.h > 40
  if (showName) return null // tooltip only for tiny tiles

  const valueText = isCompany
    ? `${rect.value.toLocaleString()}건`
    : `${rect.percentage.toFixed(1)}%`

  return (
    <div
      className="absolute z-50 px-2.5 py-1.5 rounded-md text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none"
      style={{
        background: 'rgba(30,30,30,0.92)',
        color: '#fff',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        transition: 'opacity 0.15s ease',
      }}
    >
      {rect.name} &middot; {valueText}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  TreeMapChart component                                             */
/* ------------------------------------------------------------------ */

const CONTAINER_H = 520

export function TreeMapChart({ data }: TreeMapChartProps) {
  const [groupMode, setGroupMode] = useState<'segment' | 'company'>('segment')
  const [drillSegment, setDrillSegment] = useState<string | null>(null)
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [selectedPositions, setSelectedPositions] = useState<string[]>([])

  /* ---- aggregate by segment ---- */
  const segmentMap = useMemo(() => {
    const map = new Map<string, { total: number; companies: Map<string, number> }>()
    for (const d of data) {
      if (!map.has(d.segment)) map.set(d.segment, { total: 0, companies: new Map() })
      const seg = map.get(d.segment)!
      seg.total += d.weeklyCount
      seg.companies.set(d.company, (seg.companies.get(d.company) ?? 0) + d.weeklyCount)
    }
    return map
  }, [data])

  /* ---- items for top-level segment view ---- */
  const segmentItems = useMemo<TreeItem[]>(() => {
    const items: TreeItem[] = []
    for (const [name, info] of segmentMap) {
      items.push({ name, value: info.total, color: getSegmentColor(name) })
    }
    return items.sort((a, b) => b.value - a.value)
  }, [segmentMap])

  /* ---- items for drill-down (companies within a segment) ---- */
  const drillItems = useMemo<TreeItem[]>(() => {
    if (!drillSegment) return []
    const seg = segmentMap.get(drillSegment)
    if (!seg) return []
    const parentColor = getSegmentColor(drillSegment)
    const items: TreeItem[] = []
    for (const [company, count] of seg.companies) {
      items.push({ name: company, value: count, color: parentColor, segment: drillSegment })
    }
    return items.sort((a, b) => b.value - a.value)
  }, [drillSegment, segmentMap])

  /* ---- items for flat company view ---- */
  const companyItems = useMemo<TreeItem[]>(() => {
    const map = new Map<string, { total: number; segment: string }>()
    for (const d of data) {
      const key = `${d.company}__${d.segment}`
      if (!map.has(key)) map.set(key, { total: 0, segment: d.segment })
      map.get(key)!.total += d.weeklyCount
    }
    const items: TreeItem[] = []
    for (const [key, info] of map) {
      const company = key.split('__')[0]
      items.push({
        name: company,
        value: info.total,
        color: getSegmentColor(info.segment),
        segment: info.segment,
      })
    }
    return items.sort((a, b) => b.value - a.value)
  }, [data])

  /* ---- pick which items to layout ---- */
  const activeItems = useMemo(() => {
    if (groupMode === 'company') return companyItems
    if (drillSegment) return drillItems
    return segmentItems
  }, [groupMode, drillSegment, segmentItems, drillItems, companyItems])

  /* ---- compute layout (we use a fixed width placeholder; actual width is 100%) ---- */
  /* Layout is computed in normalised 0-1 space, then mapped via % */
  const rects = useMemo(() => {
    return squarify(activeItems, { x: 0, y: 0, w: 1000, h: CONTAINER_H })
  }, [activeItems])

  const totalLayoutW = 1000 // matches bounds.w above

  const isCompany = groupMode === 'company' || drillSegment !== null

  const handleTileClick = useCallback(
    (rect: LayoutRect) => {
      if (groupMode === 'segment' && !drillSegment) {
        // Level 1 → Level 2: drill into segment
        setDrillSegment(rect.name)
        setSelectedCompany(null)
        setSelectedPositions([])
      } else {
        // Level 2 or flat company view → show positions
        const companyData = data.find(d => d.company === rect.name)
        if (companyData) {
          setSelectedCompany(rect.name)
          setSelectedPositions(companyData.positions)
        }
      }
    },
    [groupMode, drillSegment, data],
  )

  const handleBack = useCallback(() => {
    if (selectedCompany) {
      setSelectedCompany(null)
      setSelectedPositions([])
    } else {
      setDrillSegment(null)
    }
  }, [selectedCompany])

  /* ---- empty state ---- */
  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl bg-gray-50 text-gray-400 text-sm"
        style={{ height: CONTAINER_H }}
      >
        데이터가 없습니다
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* ---- Header row: toggle + breadcrumb / back ---- */}
      <div className="flex items-center justify-between mb-3">
        {/* Toggle */}
        <div className="inline-flex rounded-lg bg-gray-100 p-0.5 text-sm">
          <button
            onClick={() => { setGroupMode('segment'); setDrillSegment(null); setSelectedCompany(null); setSelectedPositions([]) }}
            className={`px-3.5 py-1.5 rounded-md font-medium transition-all ${
              groupMode === 'segment'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            세그먼트별
          </button>
          <button
            onClick={() => { setGroupMode('company'); setDrillSegment(null); setSelectedCompany(null); setSelectedPositions([]) }}
            className={`px-3.5 py-1.5 rounded-md font-medium transition-all ${
              groupMode === 'company'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            기업별
          </button>
        </div>

        {/* Breadcrumb / back */}
        {(drillSegment || selectedCompany) && (
          <div className="flex items-center gap-2 text-sm">
            {drillSegment && (
              <span className="text-gray-500">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-sm mr-1.5"
                  style={{ background: getSegmentColor(drillSegment) }}
                />
                {drillSegment}
              </span>
            )}
            {selectedCompany && (
              <>
                {drillSegment && <span className="text-gray-300">›</span>}
                <span className="text-gray-900 font-medium">{selectedCompany}</span>
              </>
            )}
            <button
              onClick={handleBack}
              className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              뒤로 가기 &#8617;
            </button>
          </div>
        )}
      </div>

      {/* ---- Hint ---- */}
      {groupMode === 'segment' && !drillSegment && (
        <p className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" />
            <path d="M13 13l6 6" />
          </svg>
          타일을 클릭하여 상세 데이터를 확인하세요
        </p>
      )}

      {/* ---- TreeMap container ---- */}
      <div
        className="relative w-full rounded-xl overflow-hidden bg-white"
        style={{ height: CONTAINER_H }}
      >
        {rects.map((rect, i) => {
          // Convert from absolute layout coords to percentage-based positioning
          const left = `${(rect.x / totalLayoutW) * 100}%`
          const top = `${(rect.y / CONTAINER_H) * 100}%`
          const width = `${(rect.w / totalLayoutW) * 100}%`
          const height = `${(rect.h / CONTAINER_H) * 100}%`

          const isClickable = true

          return (
            <div
              key={`${rect.name}-${i}`}
              className="group absolute"
              style={{
                left,
                top,
                width,
                height,
                padding: `${GAP / 2}px`,
                transition: 'all 0.3s ease',
              }}
            >
              <div
                onClick={() => handleTileClick(rect)}
                className="relative w-full h-full rounded-md overflow-hidden"
                style={{
                  background: rect.color,
                  cursor: isClickable ? 'pointer' : 'default',
                  transition: 'filter 0.15s ease, transform 0.15s ease',
                  outline: rect.name === selectedCompany ? '3px solid rgba(0,0,0,0.4)' : 'none',
                  outlineOffset: '-3px',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.filter = 'brightness(0.88)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.filter = 'brightness(1)'
                }}
              >
                <TileLabel rect={rect} isCompany={isCompany} />
                <TileTooltip rect={rect} isCompany={isCompany} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Position listing for selected company */}
      {selectedCompany && selectedPositions.length > 0 && (
        <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-900">{selectedCompany}</h3>
              <span className="text-xs text-gray-500">진행 중인 포지션</span>
            </div>
            <button
              onClick={() => { setSelectedCompany(null); setSelectedPositions([]) }}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              닫기 ✕
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {selectedPositions.map((pos, i) => (
              <div
                key={i}
                className="px-3 py-2 bg-white rounded-lg border border-gray-200 text-sm text-gray-700"
              >
                {pos}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
