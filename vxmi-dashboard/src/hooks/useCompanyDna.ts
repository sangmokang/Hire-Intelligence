import { useQuery } from '@tanstack/react-query'
import { companyDnaApi } from '../services/companyDnaApi'

export function useCompanyDna(companyId: string | null) {
  return useQuery({
    queryKey: ['company-dna', companyId],
    queryFn: () => companyDnaApi.getDna(companyId!).then(res => res.data.data),
    enabled: !!companyId,
    staleTime: 5 * 60 * 1000, // 5분
  })
}

export function useSegmentBenchmark(segmentId: string | null) {
  return useQuery({
    queryKey: ['segment-benchmark', segmentId],
    queryFn: () => companyDnaApi.getSegmentBenchmark(segmentId!).then(res => res.data.data),
    enabled: !!segmentId,
    staleTime: 10 * 60 * 1000, // 10분
  })
}
