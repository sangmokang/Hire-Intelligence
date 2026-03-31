import { apiClient } from './apiClient'
import type { CompanyDnaResponse, SegmentBenchmark, DnaTrendResponse, DnaComparisonResponse } from '../types/companyDna'

export const companyDnaApi = {
  getDna: (companyId: string) =>
    apiClient.get<{ status: string; data: CompanyDnaResponse }>(`/api/v1/dashboard/company-dna/${companyId}`),

  getSegmentBenchmark: (segmentId: string) =>
    apiClient.get<{ status: string; data: SegmentBenchmark }>(`/api/v1/dashboard/segment-benchmark/${segmentId}`),

  getTrend: (companyId: string, weeks?: number) =>
    apiClient.get<{ status: string; data: DnaTrendResponse }>(
      `/api/v1/dashboard/company-dna/${companyId}/trend`,
      { params: { weeks: weeks ?? 12 } }
    ),

  compare: (companyA: string, companyB: string) =>
    apiClient.get<{ status: string; data: DnaComparisonResponse }>(
      '/api/v1/dashboard/company-dna/compare',
      { params: { company_a: companyA, company_b: companyB } }
    ),
}
