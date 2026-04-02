export interface OppAlertTriggers {
  otwIncrease: number
  newPostings: number
  hiringWeeks: number
  sdRatio: number
}

export interface OppAlertItem {
  id: string
  companyId: string
  companyName: string
  segment: string
  oppScore: number
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM'
  triggers: OppAlertTriggers
  detectedAt: string
}

export interface OppAlertListResponse {
  items: OppAlertItem[]
  total: number
  generatedAt: string
}
