import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell,
} from 'recharts'
import { getJdInsights } from '../../services/jdInsightsApi'
import { CRAWLER_SEGMENTS } from '../../data/segments'
import { ChartSkeleton } from '../common/LoadingSkeleton'
import { ErrorBoundary } from '../common/ErrorBoundary'

const SEGMENT_LABELS: Record<string, string> = {
  dev_server:   '서버/백엔드',
  dev_frontend: '프론트엔드',
  dev_devops:   'DevOps',
  dev_mlai:     'ML/AI',
  dev_java:     'Java',
  dev_cto:      'CTO/VP',
  dev_total:    '개발 전체',
  design:       '디자인',
  pm_po:        'PM/PO',
  marketing:    '마케팅',
  hr:           'HR',
  cfo_finance:  '재무/CFO',
  sales:        '영업',
  strategy:     '전략/기획',
}

const WEEKS_OPTIONS: { label: string; value: number }[] = [
  { label: '4주', value: 4 },
  { label: '12주', value: 12 },
  { label: '26주', value: 26 },
]

const PIE_COLORS = [
  '#378ADD', '#1D9E75', '#E24B4A', '#D4537E', '#888780',
  '#BA7517', '#7F77DD', '#5DCAA5', '#F0997B', '#D85A30',
]

export function JdInsightsView() {
  const [segmentId, setSegmentId] = useState<string>('')
  const [weeks, setWeeks] = useState<number>(12)

  const { data, isLoading, error } = useQuery({
    queryKey: ['jdInsights', segmentId, weeks] as const,
    queryFn: () => getJdInsights({ segmentId: segmentId || undefined, weeks }),
    staleTime: 1000 * 60 * 10, // 10분
  })

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-xl font-semibold text-gray-900">JD 인사이트</h1>
          <p className="mt-1 text-sm text-gray-500">
            채용 공고 데이터를 분석하여 기술 스택 트렌드, 경력 분포, 연봉 벤치마크를 제공합니다.
          </p>
        </div>

        {/* Filters */}
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-3">
          <div className="flex flex-wrap items-end gap-3">
            {/* Segment selector */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">세그먼트</label>
              <select
                value={segmentId}
                onChange={(e) => setSegmentId(e.target.value)}
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 min-w-[160px]"
              >
                <option value="">전체</option>
                {CRAWLER_SEGMENTS.map((seg) => (
                  <option key={seg} value={seg}>{SEGMENT_LABELS[seg] ?? seg}</option>
                ))}
              </select>
            </div>

            {/* Weeks selector */}
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500">기간</label>
              <div className="flex gap-1">
                {WEEKS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setWeeks(opt.value)}
                    className={[
                      'px-3 py-1.5 text-xs rounded-md border transition-colors',
                      weeks === opt.value
                        ? 'bg-gray-900 text-white border-gray-900'
                        : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100',
                    ].join(' ')}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Summary badge */}
        {data && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">분석된 JD:</span>
            <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-sm font-medium">
              {data.totalAnalyzed.toLocaleString()}건
            </span>
          </div>
        )}

        {/* Tech Stack Trends */}
        <section className="bg-white rounded-xl border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">기술 스택 트렌드 (Top 10)</h2>
          {isLoading ? (
            <ChartSkeleton height={280} />
          ) : error ? (
            <p className="text-sm text-red-500 py-8 text-center">데이터를 불러오지 못했습니다.</p>
          ) : !data || data.techTrends.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">기술 스택 데이터가 없습니다.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={data.techTrends.slice(0, 10)}
                layout="vertical"
                margin={{ top: 0, right: 40, bottom: 0, left: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} />
                <Tooltip
                  formatter={(value: unknown) => [Number(value).toLocaleString(), '공고 수']}
                />
                <Bar dataKey="count" fill="#378ADD" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>

        {/* Experience Distribution + Domain Tags row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Experience Distribution */}
          <section className="bg-white rounded-xl border border-gray-100 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">경력 분포</h2>
            {isLoading ? (
              <ChartSkeleton height={240} />
            ) : error ? (
              <p className="text-sm text-red-500 py-8 text-center">데이터를 불러오지 못했습니다.</p>
            ) : !data || data.experienceDistribution.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">경력 분포 데이터가 없습니다.</p>
            ) : (
              <div className="flex items-center gap-4">
                <ResponsiveContainer width="60%" height={200}>
                  <PieChart>
                    <Pie
                      data={data.experienceDistribution}
                      dataKey="count"
                      nameKey="level"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      innerRadius={40}
                    >
                      {data.experienceDistribution.map((_, idx) => (
                        <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: unknown, name: unknown) => [
                        Number(value).toLocaleString(),
                        String(name),
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <ul className="flex-1 space-y-2">
                  {data.experienceDistribution.map((item, idx) => (
                    <li key={item.level} className="flex items-center gap-2 text-xs">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: PIE_COLORS[idx % PIE_COLORS.length] }}
                      />
                      <span className="flex-1 text-gray-700">{item.level}</span>
                      <span className="text-gray-500">{item.percentage.toFixed(1)}%</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* Top Domain Tags */}
          <section className="bg-white rounded-xl border border-gray-100 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">도메인 태그 Top 10</h2>
            {isLoading ? (
              <ChartSkeleton height={240} />
            ) : error ? (
              <p className="text-sm text-red-500 py-8 text-center">데이터를 불러오지 못했습니다.</p>
            ) : !data || data.topDomainTags.length === 0 ? (
              <p className="text-sm text-gray-400 py-8 text-center">도메인 태그 데이터가 없습니다.</p>
            ) : (
              <div className="space-y-2">
                {data.topDomainTags.slice(0, 10).map((tag, idx) => {
                  const maxCount = data.topDomainTags[0]?.count ?? 1
                  const pct = (tag.count / maxCount) * 100
                  return (
                    <div key={tag.name} className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-4 text-right shrink-0">{idx + 1}</span>
                      <span className="text-xs text-gray-700 w-24 truncate shrink-0">{tag.name}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-blue-400 h-2 rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-10 text-right shrink-0">
                        {tag.count.toLocaleString()}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </section>
        </div>

        {/* Salary Benchmarks */}
        <section className="bg-white rounded-xl border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">연봉 벤치마크 (세그먼트별)</h2>
          {isLoading ? (
            <ChartSkeleton height={280} />
          ) : error ? (
            <p className="text-sm text-red-500 py-8 text-center">데이터를 불러오지 못했습니다.</p>
          ) : !data || data.salaryBenchmarks.length === 0 ? (
            <p className="text-sm text-gray-400 py-8 text-center">연봉 데이터가 없습니다.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={data.salaryBenchmarks.filter(
                  (b) => b.salaryMin !== null || b.salaryAvg !== null || b.salaryMax !== null
                )}
                margin={{ top: 0, right: 20, bottom: 40, left: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" />
                <XAxis
                  dataKey="segmentName"
                  tick={{ fontSize: 10 }}
                  angle={-30}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis
                  tickFormatter={(v: number) => `${(v / 10000).toFixed(0)}만`}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value: unknown, name: unknown) => {
                    const label =
                      name === 'salaryMin' ? '최솟값' :
                      name === 'salaryAvg' ? '평균' :
                      name === 'salaryMax' ? '최댓값' : String(name)
                    return [`${Number(value).toLocaleString()}만원`, label]
                  }}
                />
                <Legend
                  formatter={(value: string) =>
                    value === 'salaryMin' ? '최솟값' :
                    value === 'salaryAvg' ? '평균' :
                    value === 'salaryMax' ? '최댓값' : value
                  }
                />
                <Bar dataKey="salaryMin" fill="#93B1EB" radius={[4, 4, 0, 0]} />
                <Bar dataKey="salaryAvg" fill="#378ADD" radius={[4, 4, 0, 0]} />
                <Bar dataKey="salaryMax" fill="#1D9E75" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </section>
      </div>
    </ErrorBoundary>
  )
}
