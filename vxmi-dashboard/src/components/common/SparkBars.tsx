interface SparkBarsProps {
  data: number[]
}

export function SparkBars({ data }: SparkBarsProps) {
  const max = Math.max(...data)
  return (
    <div className="flex items-end gap-1 h-12">
      {data.map((v, i) => {
        const h = Math.max(3, Math.round((v / max) * 48))
        const isLast = i === data.length - 1
        return (
          <div
            key={i}
            className="flex-1 rounded-sm"
            style={{
              height: h,
              background: isLast ? '#E24B4A' : '#e5e7eb',
            }}
          />
        )
      })}
    </div>
  )
}
