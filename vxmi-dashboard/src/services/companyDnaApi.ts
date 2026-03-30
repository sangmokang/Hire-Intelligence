import { apiClient } from './apiClient'
import type { CompanyDnaResponse, SegmentBenchmark } from '../types/companyDna'

export const companyDnaApi = {
  getDna: (companyId: string) =>
    apiClient.get<{ status: string; data: CompanyDnaResponse }>(`/api/v1/dashboard/company-dna/${companyId}`),

  getSegmentBenchmark: (segmentId: string) =>
    apiClient.get<{ status: string; data: SegmentBenchmark }>(`/api/v1/dashboard/segment-benchmark/${segmentId}`),
}
