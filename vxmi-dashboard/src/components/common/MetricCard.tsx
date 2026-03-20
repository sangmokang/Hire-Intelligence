interface MetricCardProps {
  label: string
  value: string | number
  sub?: string
}

export function MetricCard({ label, value, sub }: MetricCardProps) {
  return (
    <div className="bg-gray-100 rounded-lg p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-medium text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}
