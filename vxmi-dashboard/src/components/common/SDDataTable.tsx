import { useState, useMemo } from 'react'
import type { EnrichedSegment } from '../../types'

type SortKey = 'name' | 'demand' | 'supply' | 'ratio' | 'otwPct' | 'demandWoW' | 'supplyWoW'
type SortDir = 'asc' | 'desc'

interface SDDataTableProps {
  segments: EnrichedSegment[]
  selectedSegmentId: string | null
  onRowSelect: (segmentId: string, segmentName: string) => void
  onRowHover: (segmentId: string | null) => void
  nameColumnLabel?: string
}

const COLUMNS: { key: SortKey | 'opportunity' | 'topCompanies'; label: string; sortable: boolean; align: 'left' | 'right' | 'center' }[] = [
  { key: 'name',         label: '세그먼트',       sortable: false, align: 'left' },
  { key: 'demand',       label: '수요 (공고수)',   sortable: true,  align: 'right' },
  { key: 'supply',       label: '공급 (인재풀)',   sortable: true,  align: 'right' },
  { key: 'ratio',        label: 'S/D Ratio',     sortable: true,  align: 'right' },
  { key: 'otwPct',       label: 'OTW%',          sortable: true,  align: 'right' },
  { key: 'opportunity',  label: '기회지대',       sortable: false, align: 'center' },
  { key: 'demandWoW',    label: '수요 WoW',      sortable: true,  align: 'right' },
  { key: 'supplyWoW',    label: '공급 WoW',      sortable: true,  align: 'right' },
  { key: 'topCompanies', label: 'Top 3 기업',    sortable: false, align: 'left' },
]

function WoWCell({ value, color }: { value: number; color: string }) {
  const isPositive = value > 0
  const isNegative = value < 0
  return (
    <div className="flex items-center justify-end gap-1.5">
      <span className={`text-xs font-medium ${isPositive ? 'text-red-500' : isNegative ? 'text-blue-500' : 'text-gray-400'}`}>
        {isPositive ? '▲' : isNegative ? '▼' : '—'}
        {Math.abs(value).toFixed(1)}%
      </span>
      <svg width="48" height="16" className="shrink-0">
        {(() => {
          const bars = [0.4, 0.6, 0.5, 0.8, 1.0].map((r) => Math.abs(value) * r)
          const max = Math.max(...bars, 1)
          return bars.map((v, i) => {
            const h = Math.max(2, Math.round((v / max) * 14))
            return (
              <rect
                key={i}
                x={i * 10}
                y={16 - h}
                width={8}
                height={h}
                rx={1}
                fill={i === bars.length - 1 ? color : color + '55'}
              />
            )
          })
        })()}
      </svg>
    </div>
  )
}

export function SDDataTable({ segments, selectedSegmentId, onRowSelect, onRowHover, nameColumnLabel = '세그먼트' }: SDDataTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('ratio')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  const handleSort = (key: string) => {
    const col = COLUMNS.find((c) => c.key === key)
    if (!col?.sortable) return
    const k = key as SortKey
    if (sortKey === k) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(k)
      setSortDir('asc')
    }
  }

  const sorted = useMemo(() => {
    const arr = [...segments]
    arr.sort((a, b) => {
      let va: number, vb: number
      switch (sortKey) {
        case 'name':      return sortDir === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name)
        case 'demand':    va = a.demand; vb = b.demand; break
        case 'supply':    va = a.supply; vb = b.supply; break
        case 'ratio':     va = a.demand / a.supply; vb = b.demand / b.supply; break
        case 'otwPct':    va = a.otwPct; vb = b.otwPct; break
        case 'demandWoW': va = a.demandWoW; vb = b.demandWoW; break
        case 'supplyWoW': va = a.supplyWoW; vb = b.supplyWoW; break
        default:          return 0
      }
      return sortDir === 'asc' ? va - vb : vb - va
    })
    return arr
  }, [segments, sortKey, sortDir])

  return (
    <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={`px-3 py-2.5 font-semibold text-gray-600 whitespace-nowrap border-r border-gray-100 last:border-r-0 ${
                    col.sortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''
                  } ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.key === 'name' ? nameColumnLabel : col.label}
                    {col.sortable && sortKey === (col.key as SortKey) && (
                      <span className="text-gray-900">{sortDir === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((seg, idx) => {
              const ratio = seg.demand / seg.supply
              const isOpportunity = ratio <= 0.2
              const isSelected = selectedSegmentId === seg.id
              return (
                <tr
                  key={seg.id}
                  onClick={() => onRowSelect(seg.id, seg.name)}
                  onMouseEnter={() => onRowHover(seg.id)}
                  onMouseLeave={() => onRowHover(null)}
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-50 ring-1 ring-inset ring-blue-200'
                      : idx % 2 === 0
                        ? 'bg-white hover:bg-gray-50'
                        : 'bg-gray-50/40 hover:bg-gray-100/60'
                  }`}
                >
                  {/* 세그먼트 */}
                  <td className="px-3 py-2 border-r border-gray-100 font-medium text-gray-900 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: seg.color }}
                      />
                      {seg.name}
                    </div>
                  </td>
                  {/* 수요 */}
                  <td className="px-3 py-2 border-r border-gray-100 text-right text-gray-700 tabular-nums">
                    {seg.demand.toLocaleString()}
                  </td>
                  {/* 공급 */}
                  <td className="px-3 py-2 border-r border-gray-100 text-right text-gray-700 tabular-nums">
                    {seg.supply.toLocaleString()}
                  </td>
                  {/* S/D Ratio */}
                  <td className={`px-3 py-2 border-r border-gray-100 text-right font-semibold tabular-nums ${
                    isOpportunity ? 'text-emerald-600' : 'text-gray-700'
                  }`}>
                    {ratio.toFixed(2)}
                  </td>
                  {/* OTW% */}
                  <td className="px-3 py-2 border-r border-gray-100 text-right text-gray-700 tabular-nums">
                    {seg.otwPct}%
                  </td>
                  {/* 기회지대 */}
                  <td className="px-3 py-2 border-r border-gray-100 text-center">
                    {isOpportunity ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        기회
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  {/* 수요 WoW */}
                  <td className="px-3 py-2 border-r border-gray-100">
                    <WoWCell value={seg.demandWoW} color={seg.demandWoW >= 0 ? '#E24B4A' : '#378ADD'} />
                  </td>
                  {/* 공급 WoW */}
                  <td className="px-3 py-2 border-r border-gray-100">
                    <WoWCell value={seg.supplyWoW} color={seg.supplyWoW >= 0 ? '#E24B4A' : '#378ADD'} />
                  </td>
                  {/* Top 3 기업 */}
                  <td className="px-3 py-2 text-gray-600">
                    <div className="flex items-center gap-1 max-w-[200px]">
                      {seg.topCompanies.map((co, ci) => (
                        <span
                          key={ci}
                          className="inline-block px-1.5 py-0.5 bg-gray-100 rounded text-[10px] text-gray-600 truncate max-w-[64px]"
                          title={co}
                        >
                          {co}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
