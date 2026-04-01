import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { fetchUsageStats } from '../../services/userService';
import type { UsageStats } from '../../services/userService';

const PIE_COLORS = ['#1f2937', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb'];

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/3" />
      <div className="h-4 bg-gray-200 rounded w-1/4" />
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="h-5 bg-gray-200 rounded w-1/4 mb-4" />
        <div className="h-48 bg-gray-100 rounded" />
      </div>
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="h-5 bg-gray-200 rounded w-1/4 mb-4" />
        <div className="h-48 bg-gray-100 rounded" />
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-400">
      <svg className="w-10 h-10 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <p className="text-sm">{message}</p>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
    </div>
  );
}

function DailyUsageChart({ data }: { data: UsageStats['dailyStats'] }) {
  if (data.length === 0) {
    return <EmptyState message="사용 데이터가 없습니다." />;
  }

  // 날짜를 MM/DD 형식으로 줄임
  const chartData = data.map((d) => ({
    ...d,
    label: d.date.slice(5), // "04-01" 형태
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: '#6b7280' }}
          interval={4}
          tickLine={false}
          axisLine={false}
        />
        <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          labelFormatter={(l) => `날짜: ${String(l)}`}
          formatter={(v) => [v, 'API 호출']}
        />
        <Bar dataKey="count" fill="#1f2937" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ViewUsageChart({ data }: { data: UsageStats['viewStats'] }) {
  if (data.length === 0) {
    return <EmptyState message="뷰 사용 데이터가 없습니다." />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="view"
          cx="50%"
          cy="50%"
          outerRadius={80}
          label={false}
        >
          {data.map((_entry, index) => (
            <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          formatter={(v) => [v, '횟수']}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12 }}
          formatter={(value) => (
            <span className="text-gray-700">{String(value)}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['me', 'usage'],
    queryFn: async () => {
      const res = await fetchUsageStats();
      return res.data.data;
    },
    staleTime: 5 * 60 * 1000, // 5분
  });

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">사용 분석</h1>
        <p className="text-sm text-gray-500 mt-1">API 사용량과 뷰 접근 통계를 확인하세요.</p>
      </div>

      {isError ? (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          데이터를 불러오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.
        </div>
      ) : null}

      {/* 요약 지표 */}
      {data && (
        <div className="grid grid-cols-2 gap-4">
          <MetricCard label="전체 API 호출 수" value={data.totalApiCalls} />
          <MetricCard label="이번 달 호출 수" value={data.currentMonthCalls} />
        </div>
      )}

      {/* 일별 API 호출 차트 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">최근 30일 API 호출 수</h2>
        {data ? (
          <DailyUsageChart data={data.dailyStats} />
        ) : (
          <EmptyState message="사용 데이터가 없습니다." />
        )}
      </div>

      {/* 뷰별 접근 통계 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">뷰별 접근 통계</h2>
        {data ? (
          <ViewUsageChart data={data.viewStats} />
        ) : (
          <EmptyState message="뷰 사용 데이터가 없습니다." />
        )}
      </div>
    </div>
  );
}
