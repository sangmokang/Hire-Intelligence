import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchDataQuality, fetchCrawlStatus } from '../../services/adminApi';
import type { DataQualityResponse, CrawlStatusResponse, WeeklyCollectionStats } from '../../services/adminApi';

// 크롤 상태 배지 색상
function crawlStatusBadge(status: string | null): React.ReactElement {
  if (!status) {
    return <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">—</span>;
  }
  const map: Record<string, string> = {
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    running: 'bg-blue-100 text-blue-700',
  };
  const cls = map[status] ?? 'bg-gray-100 text-gray-500';
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{status}</span>;
}

// 날짜 포맷 헬퍼
function formatDateTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' });
}

// 크롤 상태 카드
function CrawlStatusCard({ data }: { data: CrawlStatusResponse }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-4">크롤 상태</h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">마지막 크롤</p>
          <p className="text-sm font-medium text-gray-900">{formatDateTime(data.lastCrawlAt)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">상태</p>
          <div>{crawlStatusBadge(data.lastCrawlStatus)}</div>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">수집 / 파싱</p>
          <p className="text-sm font-medium text-gray-900">
            {data.totalCrawled.toLocaleString()} / {data.totalParsed.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">다음 스케줄</p>
          <p className="text-sm font-medium text-gray-900">{data.nextScheduled || '—'}</p>
        </div>
      </div>
    </div>
  );
}

// 크롤 상태 카드 스켈레톤
function CrawlStatusSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-24 mb-4" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i}>
            <div className="h-3 bg-gray-200 rounded w-16 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}

// 주간 수집 통계 테이블
function WeeklyStatsTable({ stats }: { stats: WeeklyCollectionStats[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-4">주간 수집 통계 (최근 4주)</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left text-xs text-gray-400 font-medium pb-2 pr-4">주차</th>
              <th className="text-right text-xs text-gray-400 font-medium pb-2 pr-4">총 공고수</th>
              <th className="text-right text-xs text-gray-400 font-medium pb-2 pr-4">기업수</th>
              <th className="text-right text-xs text-gray-400 font-medium pb-2">직군 커버리지</th>
            </tr>
          </thead>
          <tbody>
            {stats.map((row) => {
              const coverageLow = row.segmentsCovered < row.segmentsTotal;
              return (
                <tr
                  key={row.week}
                  className={`border-b border-gray-50 last:border-0 ${coverageLow ? 'bg-yellow-50' : ''}`}
                >
                  <td className="py-2 pr-4 text-gray-900 font-medium">{row.week}</td>
                  <td className="py-2 pr-4 text-right text-gray-700">{row.totalPostings.toLocaleString()}</td>
                  <td className="py-2 pr-4 text-right text-gray-700">{row.totalCompanies.toLocaleString()}</td>
                  <td className="py-2 text-right">
                    <span className={coverageLow ? 'text-yellow-600 font-medium' : 'text-gray-700'}>
                      {row.segmentsCovered}/{row.segmentsTotal}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// 주간 통계 스켈레톤
function WeeklyStatsSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-40 mb-4" />
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="flex gap-4 py-2 border-b border-gray-50">
          <div className="h-4 bg-gray-200 rounded w-20" />
          <div className="h-4 bg-gray-200 rounded w-16 ml-auto" />
          <div className="h-4 bg-gray-200 rounded w-12" />
          <div className="h-4 bg-gray-200 rounded w-10" />
        </div>
      ))}
    </div>
  );
}

// 누락 직군 리스트
function MissingSegmentsList({ segments }: { segments: string[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-4">누락 직군 (이번 주)</h2>
      {segments.length === 0 ? (
        <p className="text-xs text-green-500">모든 직군 데이터가 수집되었습니다.</p>
      ) : (
        <ul className="space-y-2">
          {segments.map((seg) => (
            <li key={seg} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
              <span className="text-sm text-gray-700">{seg}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// 이상치 알림
function AnomalyList({ anomalies }: { anomalies: DataQualityResponse['anomalies'] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-4">이상치 알림 (±50% 변동)</h2>
      {anomalies.length === 0 ? (
        <p className="text-xs text-green-500">이상치 없음.</p>
      ) : (
        <ul className="space-y-3">
          {anomalies.map((a) => {
            const isUp = a.changePct >= 0;
            return (
              <li key={`${a.week}-${a.prevWeek}`} className="flex items-start gap-2">
                <span className={`text-lg leading-none ${isUp ? 'text-green-500' : 'text-red-500'}`}>
                  {isUp ? '↑' : '↓'}
                </span>
                <div>
                  <p className="text-sm text-gray-800 font-medium">{a.week}</p>
                  <p className="text-xs text-gray-400">
                    전주 {a.prevTotalPostings.toLocaleString()} → 이번 주 {a.currTotalPostings.toLocaleString()}
                    {' '}
                    <span className={isUp ? 'text-green-500' : 'text-red-500'}>
                      ({isUp ? '+' : ''}{a.changePct.toFixed(1)}%)
                    </span>
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

// 하단 패널 스켈레톤
function BottomPanelSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-32 mb-4" />
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-2 py-1.5">
          <div className="w-2 h-2 rounded-full bg-gray-200 flex-shrink-0" />
          <div className="h-4 bg-gray-200 rounded w-28" />
        </div>
      ))}
    </div>
  );
}

export function AdminDataView() {
  const {
    data: qualityData,
    isLoading: qualityLoading,
    error: qualityError,
  } = useQuery<DataQualityResponse>({
    queryKey: ['admin', 'data-quality'],
    queryFn: fetchDataQuality,
  });

  const {
    data: crawlData,
    isLoading: crawlLoading,
    error: crawlError,
  } = useQuery<CrawlStatusResponse>({
    queryKey: ['admin', 'crawl-status'],
    queryFn: fetchCrawlStatus,
  });

  return (
    <div>
      <h1 className="text-lg font-semibold text-gray-900 mb-6">데이터 모니터링</h1>

      {/* 크롤 상태 카드 */}
      {crawlLoading && <CrawlStatusSkeleton />}
      {crawlError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <p className="text-sm text-red-500">크롤 상태를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</p>
        </div>
      )}
      {crawlData && <CrawlStatusCard data={crawlData} />}

      {/* 주간 수집 통계 테이블 */}
      {qualityLoading && <WeeklyStatsSkeleton />}
      {qualityError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <p className="text-sm text-red-500">데이터 품질 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.</p>
        </div>
      )}
      {qualityData && (
        <>
          <WeeklyStatsTable stats={qualityData.weeklyStats.slice(0, 4)} />

          {/* 누락 직군 / 이상치 알림 */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {qualityLoading ? (
              <>
                <BottomPanelSkeleton />
                <BottomPanelSkeleton />
              </>
            ) : (
              <>
                <MissingSegmentsList segments={qualityData.missingSegments} />
                <AnomalyList anomalies={qualityData.anomalies} />
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
