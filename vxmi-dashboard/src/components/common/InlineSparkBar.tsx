interface InlineSparkBarProps {
  data: number[]
  color?: string
}

export function InlineSparkBar({ data, color = '#378ADD' }: InlineSparkBarProps) {
  const max = Math.max(...data)
  const w = 80
  const h = 24
  const barW = Math.floor((w - (data.length - 1) * 1) / data.length)
  return (
    <svg width={w} height={h} style={{ display: 'block' }}>
      {data.map((v, i) => {
        const barH = Math.max(2, Math.round((v / max) * h))
        const isLast = i === data.length - 1
        return (
          <rect
            key={i}
            x={i * (barW + 1)}
            y={h - barH}
            width={barW}
            height={barH}
            rx={1}
            fill={isLast ? '#E24B4A' : color + '88'}
          />
        )
      })}
    </svg>
  )
}
