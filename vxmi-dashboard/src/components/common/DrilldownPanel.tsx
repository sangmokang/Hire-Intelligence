import type { DrilldownItem } from '../../types'

interface DrilldownPanelProps {
  segmentName: string | null
  items: DrilldownItem[]
  onClose: () => void
}

export function DrilldownPanel({ segmentName, items, onClose }: DrilldownPanelProps) {
  if (!segmentName) return null

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-xl border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">{segmentName} — 주요 채용 기업</h3>
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-900">
          닫기
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {items.map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-2 bg-white rounded-md border border-gray-200 text-sm"
          >
            <span className="font-medium min-w-[100px] text-gray-900">{item.company}</span>
            <span className="text-gray-500 flex-1">{item.position}</span>
            <span className="text-xs text-gray-500">{item.count}건</span>
          </div>
        ))}
      </div>
    </div>
  )
}
