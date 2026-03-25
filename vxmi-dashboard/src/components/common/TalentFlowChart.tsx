import { useState } from 'react'
import type { TalentFlow } from '../../types'

interface Props {
  talentFlow: TalentFlow
  companyName: string
}

interface RowLayout {
  x: number
  y: number
  width: number
  height: number
  count: number
  company: string
}

const ROW_H = 36
const ROW_GAP = 8
const COL_W = 160
const CENTER_X = 200
const CENTER_W = 120
const RIGHT_X = 360
const SVG_W = 520
const BAND_OPACITY = 0.18
const BAND_OPACITY_HOVER = 0.45


function CurvedBand({
  from,
  to,
  color,
  isLeft,
  hovered,
  onEnter,
  onLeave,
}: {
  from: RowLayout
  to: { x: number; y: number; height: number }
  color: string
  isLeft: boolean
  hovered: boolean
  onEnter: () => void
  onLeave: () => void
}) {
  // Band thickness scales with row height (proportional to count)
  const thickness = from.height
  const fromCx = isLeft ? from.x + from.width : from.x
  const fromCy = from.y + from.height / 2
  const toCx = isLeft ? to.x : to.x + CENTER_W
  const toCy = to.y + to.height / 2

  const midX = (fromCx + toCx) / 2

  // Top path edge
  const topFrom = fromCy - thickness / 2
  const topTo = toCy - thickness / 2
  // Bottom path edge
  const botFrom = fromCy + thickness / 2
  const botTo = toCy + thickness / 2

  const d = [
    `M ${fromCx} ${topFrom}`,
    `C ${midX} ${topFrom}, ${midX} ${topTo}, ${toCx} ${topTo}`,
    `L ${toCx} ${botTo}`,
    `C ${midX} ${botTo}, ${midX} ${botFrom}, ${fromCx} ${botFrom}`,
    'Z',
  ].join(' ')

  return (
    <path
      d={d}
      fill={color}
      opacity={hovered ? BAND_OPACITY_HOVER : BAND_OPACITY}
      style={{ transition: 'opacity 0.18s ease', cursor: 'pointer' }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    />
  )
}

export function TalentFlowChart({ talentFlow, companyName }: Props) {
  const { inflow, outflow, totalInflow = 0, totalOutflow = 0, netChange = 0 } = talentFlow
  const [hoveredLeft, setHoveredLeft] = useState<number | null>(null)
  const [hoveredRight, setHoveredRight] = useState<number | null>(null)

  const maxCount = Math.max(
    ...inflow.map((i: { count: number }) => i.count),
    ...outflow.map((o: { count: number }) => o.count)
  )

  const totalRows = Math.max(inflow.length, outflow.length)

  // Build row layouts — rows scale height by count
  function buildScaledRows(
    items: { company: string; count: number }[],
    x: number
  ): RowLayout[] {
    const totalH = totalRows * (ROW_H + ROW_GAP) - ROW_GAP
    let cursor = 0
    return items.map((item) => {
      const proportion = item.count / totalInflow  // rough proportional height
      const h = Math.max(24, Math.round(proportion * totalH * 0.8 + ROW_H * 0.2))
      const row: RowLayout = {
        x,
        y: cursor,
        width: COL_W,
        height: h,
        count: item.count,
        company: item.company,
      }
      cursor += h + ROW_GAP
      return row
    })
  }

  const inflowRows = buildScaledRows(inflow, 0)
  const outflowRows = buildScaledRows(outflow, RIGHT_X)

  const actualInflowH = inflowRows.reduce((s, r) => s + r.height + ROW_GAP, 0) - ROW_GAP
  const actualOutflowH = outflowRows.reduce((s, r) => s + r.height + ROW_GAP, 0) - ROW_GAP
  const actualH = Math.max(actualInflowH, actualOutflowH)

  // Center anchor — distribute anchor points proportionally across center height
  const centerAnchorY = actualH / 2
  const centerAnchorH = actualH * 0.7

  function centerAnchor(rows: RowLayout[], idx: number) {
    const total = rows.length
    const slotH = centerAnchorH / total
    return {
      x: CENTER_X,
      y: centerAnchorY - centerAnchorH / 2 + idx * slotH + slotH / 2 - rows[idx].height / 2,
      height: rows[idx].height,
    }
  }

  const isPositive = (netChange ?? 0) >= 0

  return (
    <div className="w-full">
      {/* Summary stats row */}
      <div className="flex items-center gap-6 mb-5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-sky-400" />
          <span className="text-xs text-gray-500">유입</span>
          <span className="text-sm font-medium text-gray-900">+{totalInflow}명</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-rose-400" />
          <span className="text-xs text-gray-500">유출</span>
          <span className="text-sm font-medium text-gray-900">-{totalOutflow}명</span>
        </div>
        <div className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-full border"
          style={{
            borderColor: isPositive ? '#86efac' : '#fca5a5',
            background: isPositive ? '#f0fdf4' : '#fff1f2',
          }}
        >
          <span className="text-xs font-medium" style={{ color: isPositive ? '#16a34a' : '#e11d48' }}>
            {isPositive ? '▲' : '▼'} 순유입 {isPositive ? '+' : ''}{netChange}명
          </span>
        </div>
      </div>

      {/* Column headers */}
      <div className="flex items-center mb-3" style={{ paddingLeft: 0 }}>
        <div style={{ width: COL_W }} className="text-xs font-medium text-sky-500 tracking-wide uppercase">
          유입 출신기업
        </div>
        <div style={{ width: CENTER_X - COL_W + CENTER_W }} />
        <div style={{ width: COL_W }} className="text-xs font-medium text-rose-400 tracking-wide uppercase text-right">
          이직 기업
        </div>
      </div>

      {/* Main flow diagram */}
      <div className="relative w-full overflow-x-auto">
        <svg
          width={SVG_W}
          height={actualH}
          viewBox={`0 0 ${SVG_W} ${actualH}`}
          className="w-full"
          style={{ maxWidth: SVG_W, display: 'block' }}
        >
          {/* Inflow bands */}
          {inflowRows.map((row, i) => (
            <CurvedBand
              key={`in-${i}`}
              from={row}
              to={centerAnchor(inflowRows, i)}
              color="#0ea5e9"
              isLeft={true}
              hovered={hoveredLeft === i}
              onEnter={() => setHoveredLeft(i)}
              onLeave={() => setHoveredLeft(null)}
            />
          ))}

          {/* Outflow bands */}
          {outflowRows.map((row, i) => (
            <CurvedBand
              key={`out-${i}`}
              from={row}
              to={centerAnchor(outflowRows, i)}
              color="#f43f5e"
              isLeft={false}
              hovered={hoveredRight === i}
              onEnter={() => setHoveredRight(i)}
              onLeave={() => setHoveredRight(null)}
            />
          ))}

          {/* Inflow row pills */}
          {inflowRows.map((row, i) => {
            const barMaxW = COL_W - 8
            const barW = Math.max(16, Math.round((row.count / maxCount) * barMaxW))
            const isHov = hoveredLeft === i
            return (
              <g
                key={`inrow-${i}`}
                onMouseEnter={() => setHoveredLeft(i)}
                onMouseLeave={() => setHoveredLeft(null)}
                style={{ cursor: 'default' }}
              >
                {/* Background pill */}
                <rect
                  x={row.x}
                  y={row.y}
                  width={row.width}
                  height={row.height}
                  rx={6}
                  fill={isHov ? '#e0f2fe' : '#f8fafc'}
                  stroke={isHov ? '#7dd3fc' : '#e2e8f0'}
                  strokeWidth={1}
                  style={{ transition: 'fill 0.15s, stroke 0.15s' }}
                />
                {/* Count bar fill */}
                <rect
                  x={row.x + 2}
                  y={row.y + row.height - 5}
                  width={barW}
                  height={3}
                  rx={1.5}
                  fill="#38bdf8"
                  opacity={0.7}
                />
                {/* Company name */}
                <text
                  x={row.x + 10}
                  y={row.y + row.height / 2 - 3}
                  fontSize={11}
                  fontWeight={isHov ? 600 : 400}
                  fill={isHov ? '#0369a1' : '#374151'}
                  dominantBaseline="middle"
                  style={{ transition: 'fill 0.15s' }}
                >
                  {row.company}
                </text>
                {/* Count */}
                <text
                  x={row.x + row.width - 10}
                  y={row.y + row.height / 2 - 3}
                  fontSize={11}
                  fontWeight={500}
                  fill="#0ea5e9"
                  textAnchor="end"
                  dominantBaseline="middle"
                >
                  +{row.count}
                </text>
              </g>
            )
          })}

          {/* Outflow row pills */}
          {outflowRows.map((row, i) => {
            const barMaxW = COL_W - 8
            const barW = Math.max(16, Math.round((row.count / maxCount) * barMaxW))
            const isHov = hoveredRight === i
            return (
              <g
                key={`outrow-${i}`}
                onMouseEnter={() => setHoveredRight(i)}
                onMouseLeave={() => setHoveredRight(null)}
                style={{ cursor: 'default' }}
              >
                <rect
                  x={row.x}
                  y={row.y}
                  width={row.width}
                  height={row.height}
                  rx={6}
                  fill={isHov ? '#fff1f2' : '#f8fafc'}
                  stroke={isHov ? '#fda4af' : '#e2e8f0'}
                  strokeWidth={1}
                  style={{ transition: 'fill 0.15s, stroke 0.15s' }}
                />
                {/* Count bar fill */}
                <rect
                  x={row.x + 2}
                  y={row.y + row.height - 5}
                  width={barW}
                  height={3}
                  rx={1.5}
                  fill="#fb7185"
                  opacity={0.7}
                />
                {/* Company name */}
                <text
                  x={row.x + 10}
                  y={row.y + row.height / 2 - 3}
                  fontSize={11}
                  fontWeight={isHov ? 600 : 400}
                  fill={isHov ? '#be123c' : '#374151'}
                  dominantBaseline="middle"
                  style={{ transition: 'fill 0.15s' }}
                >
                  {row.company}
                </text>
                {/* Count */}
                <text
                  x={row.x + row.width - 10}
                  y={row.y + row.height / 2 - 3}
                  fontSize={11}
                  fontWeight={500}
                  fill="#f43f5e"
                  textAnchor="end"
                  dominantBaseline="middle"
                >
                  -{row.count}
                </text>
              </g>
            )
          })}

          {/* Center company badge */}
          <g>
            {/* Vertical spine line */}
            <line
              x1={CENTER_X + CENTER_W / 2}
              y1={0}
              x2={CENTER_X + CENTER_W / 2}
              y2={actualH}
              stroke="#e2e8f0"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
            {/* Center badge background */}
            <rect
              x={CENTER_X}
              y={actualH / 2 - 28}
              width={CENTER_W}
              height={56}
              rx={10}
              fill="#1e293b"
            />
            {/* Company name in center */}
            <text
              x={CENTER_X + CENTER_W / 2}
              y={actualH / 2 - 6}
              fontSize={13}
              fontWeight={700}
              fill="#f8fafc"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {companyName}
            </text>
            {/* Net change label */}
            <text
              x={CENTER_X + CENTER_W / 2}
              y={actualH / 2 + 13}
              fontSize={10}
              fontWeight={500}
              fill={isPositive ? '#86efac' : '#fca5a5'}
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {isPositive ? '▲' : '▼'} {isPositive ? '+' : ''}{netChange}
            </text>
          </g>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-1.5">
          <div className="w-8 h-1.5 rounded-full" style={{ background: 'linear-gradient(90deg, #38bdf8, #0ea5e9)' }} />
          <span className="text-xs text-gray-400">인재 유입</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-8 h-1.5 rounded-full" style={{ background: 'linear-gradient(90deg, #fb7185, #f43f5e)' }} />
          <span className="text-xs text-gray-400">인재 유출</span>
        </div>
        <span className="text-xs text-gray-300 ml-auto">최근 12개월 · LinkedIn 기반</span>
      </div>
    </div>
  )
}
