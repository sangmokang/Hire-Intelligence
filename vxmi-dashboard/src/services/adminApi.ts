import { apiClient } from './apiClient';

// 데이터 품질 모니터링
export interface WeeklyCollectionStats {
  week: string;
  totalPostings: number;
  totalCompanies: number;
  segmentsCovered: number;
  segmentsTotal: number;
}

export interface DataQualityResponse {
  currentWeek: string;
  weeklyStats: WeeklyCollectionStats[];
  missingSegments: string[];
  anomalies: Array<{
    week: string;
    prevWeek: string;
    prevTotalPostings: number;
    currTotalPostings: number;
    changePct: number;
  }>;
}

export interface CrawlStatusResponse {
  lastCrawlAt: string | null;
  lastCrawlStatus: string | null;
  totalCrawled: number;
  totalParsed: number;
  nextScheduled: string;
}

export const fetchDataQuality = async (): Promise<DataQualityResponse> => {
  const res = await apiClient.get('/admin/data-quality');
  return res.data.data;
};

export const fetchCrawlStatus = async (): Promise<CrawlStatusResponse> => {
  const res = await apiClient.get('/admin/crawl-status');
  return res.data.data;
};
