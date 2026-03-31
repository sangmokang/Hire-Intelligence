import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { DnaTrendPoint } from '../../types/companyDna'

interface DnaTrendChartProps {
  dataPoints: DnaTrendPoint[]
  companyName: string
}

const LINES = [
  { key: 'overallScore', name: '종합', color: '#6366f1', strokeWidth: 3 },
  { key: 'techScore', name: '기술', color: '#10b981' },
  { key: 'hiringScore', name: '채용', color: '#f59e0b' },
  { key: 'salaryPct', name: '연봉', color: '#ef4444' },
  { key: 'cultureScore', name: '문화', color: '#8b5cf6' },
]

export default function DnaTrendChart({ dataPoints, companyName }: DnaTrendChartProps) {
  // week format: "2026-W13" → "W13"로 축약
  const data = dataPoints.map(p => ({
    ...p,
    weekLabel: p.week.split('-')[1] || p.week,
  }))

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="weekLabel" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(value: unknown, name: unknown) => [`${Number(value)?.toFixed(1) ?? '-'}점`, String(name)]}
            labelFormatter={(label: unknown) => `${companyName} — ${label}`}
          />
          <Legend />
          {LINES.map(line => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              name={line.name}
              stroke={line.color}
              strokeWidth={line.strokeWidth ?? 1.5}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
