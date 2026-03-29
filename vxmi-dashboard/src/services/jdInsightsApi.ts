import { apiClient } from './apiClient'
import type { JdInsightsResponse } from '../types/jdInsights'

interface JdInsightsParams {
  segmentId?: string
  weeks?: number
}

export async function getJdInsights(params: JdInsightsParams = {}): Promise<JdInsightsResponse> {
  const response = await apiClient.get('/api/v1/dashboard/jd-insights', {
    params: {
      segment_id: params.segmentId,
      weeks: params.weeks,
    },
  })
  return response.data.data
}
