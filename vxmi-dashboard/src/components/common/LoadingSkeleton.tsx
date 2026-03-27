interface SkeletonProps {
  className?: string;
}

function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  );
}

// Card skeleton for metric cards
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-3 w-16" />
    </div>
  );
}

// Table skeleton for data tables
export function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 flex gap-4">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-16" />
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="px-5 py-3 border-b border-gray-50 flex gap-4 items-center">
          <Skeleton className="h-4 w-6" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-14" />
        </div>
      ))}
    </div>
  );
}

// Chart skeleton for visualizations
export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5">
      <Skeleton className="h-4 w-32 mb-4" />
      <div
        className="relative flex items-end gap-2 px-2"
        style={{ height: `${height}px` }}
      >
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 animate-pulse bg-gray-200 rounded-t"
            style={{ height: `${(i * 17 + 30) % 60 + 20}%` }}
          />
        ))}
      </div>
    </div>
  );
}

// Dashboard view skeleton (full page)
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
      {/* Chart */}
      <ChartSkeleton height={320} />
      {/* Table */}
      <TableSkeleton rows={6} />
    </div>
  );
}
