import { apiClient } from './apiClient';
import type { ApiResponse } from '../types/api';
import type {
  SDMatrixItem,
  CompanyRankItem,
  CompanyTimeline,
  SegmentTrend,
  ResumeMatchInput,
  ResumeMatchOutput,
  CompanyProfile,
} from '../types/dashboard';

export interface TimelineParams {
  mode: string;
  weeks: number;
  topN: number;
  segments?: string[];
  companyIds?: string[];
}

export const dashboardService = {
  // S/D Matrix
  async getSDMatrix(week?: string, viewMode?: string): Promise<ApiResponse<SDMatrixItem[]>> {
    const params: Record<string, string> = {};
    if (week) params.week = week;
    if (viewMode) params.viewMode = viewMode;
    const { data } = await apiClient.get('/api/v1/dashboard/sd-matrix', { params });
    return data;
  },

  // Top Companies
  async getTopCompanies(week?: string, limit = 20): Promise<ApiResponse<CompanyRankItem[]>> {
    const params: Record<string, string | number> = { limit };
    if (week) params.week = week;
    const { data } = await apiClient.get('/api/v1/dashboard/companies', { params });
    return data;
  },

  // Company Timeline
  async getCompanyTimeline(params: TimelineParams): Promise<ApiResponse<CompanyTimeline[]>> {
    const { data } = await apiClient.get('/api/v1/dashboard/timeline', { params });
    return data;
  },

  // Hiring Trends
  async getHiringTrends(weeks: number, segments: string[]): Promise<ApiResponse<SegmentTrend[]>> {
    const { data } = await apiClient.get('/api/v1/dashboard/trends', {
      params: { weeks, segments: segments.join(',') },
    });
    return data;
  },

  // Resume Match (POST)
  async postResumeMatch(input: ResumeMatchInput): Promise<ApiResponse<ResumeMatchOutput>> {
    const { data } = await apiClient.post('/api/v1/dashboard/resume-match', input);
    return data;
  },

  // Company Analysis
  async getCompanyAnalysis(companyId: string): Promise<ApiResponse<CompanyProfile>> {
    const { data } = await apiClient.get(`/api/v1/dashboard/company-analysis/${companyId}`);
    return data;
  },
};
