interface SubIndexBarProps {
  label: string
  value: number
}

export function SubIndexBar({ label, value }: SubIndexBarProps) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="text-xs text-gray-500 min-w-[70px]">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 rounded overflow-hidden">
        <div
          className="h-full rounded bg-blue-500"
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 min-w-[28px] text-right">{value}</span>
    </div>
  )
}
