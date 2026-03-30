import { useQuery, useMutation } from '@tanstack/react-query';
import { dashboardService, type TimelineParams } from '../services/dashboardService';
import type { ResumeMatchInput } from '../types/dashboard';

// Query key factory
export const dashboardKeys = {
  all: ['dashboard'] as const,
  sdMatrix: (week?: string, viewMode?: string) =>
    ['dashboard', 'sd-matrix', week, viewMode] as const,
  sdMatrixDrilldown: (segmentId: string, week?: string) =>
    ['dashboard', 'sd-matrix-drilldown', segmentId, week] as const,
  topCompanies: (week?: string, limit?: number) =>
    ['dashboard', 'top-companies', week, limit] as const,
  companyTimeline: (params: TimelineParams) =>
    ['dashboard', 'company-timeline', params] as const,
  hiringTrends: (weeks: number, segments: string[]) =>
    ['dashboard', 'hiring-trends', weeks, segments] as const,
  companyAnalysis: (companyId: string) =>
    ['dashboard', 'company-analysis', companyId] as const,
};

// S/D Matrix query
export function useSDMatrix(week?: string, viewMode?: string) {
  return useQuery({
    queryKey: dashboardKeys.sdMatrix(week, viewMode),
    queryFn: () => dashboardService.getSDMatrix(week, viewMode),
    staleTime: 1000 * 60 * 60, // 1 hour (weekly data)
  });
}

// Top Companies query
export function useTopCompanies(week?: string, limit = 20) {
  return useQuery({
    queryKey: dashboardKeys.topCompanies(week, limit),
    queryFn: () => dashboardService.getTopCompanies(week, limit),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

// Company Timeline query
export function useCompanyTimeline(params: TimelineParams) {
  return useQuery({
    queryKey: dashboardKeys.companyTimeline(params),
    queryFn: () => dashboardService.getCompanyTimeline(params),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

// Hiring Trends query
export function useHiringTrends(weeks: number, segments: string[]) {
  return useQuery({
    queryKey: dashboardKeys.hiringTrends(weeks, segments),
    queryFn: () => dashboardService.getHiringTrends(weeks, segments),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: segments.length > 0,
  });
}

// Resume Match mutation
export function useResumeMatch() {
  return useMutation({
    mutationFn: (input: ResumeMatchInput) => dashboardService.postResumeMatch(input),
  });
}

// SD Matrix Drilldown query
export function useSDMatrixDrilldown(segmentId: string | null, week?: string) {
  return useQuery({
    queryKey: dashboardKeys.sdMatrixDrilldown(segmentId ?? '', week),
    queryFn: () => dashboardService.getSDMatrixDrilldown(segmentId!, week),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: Boolean(segmentId),
  });
}

// Company Analysis query
export function useCompanyAnalysis(companyId: string) {
  return useQuery({
    queryKey: dashboardKeys.companyAnalysis(companyId),
    queryFn: () => dashboardService.getCompanyAnalysis(companyId),
    staleTime: 1000 * 60 * 30, // 30 minutes
    enabled: Boolean(companyId),
  });
}
