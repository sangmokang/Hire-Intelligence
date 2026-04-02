export interface ApplicationDirection {
  type: 'UPWARD' | 'LATERAL' | 'DOWNWARD'
  candidateTds: number
  targetCompanyTds: number | null
  deltaPercent: number | null
}

export interface SalaryNegotiation {
  marketP25: number
  marketP50: number
  marketP75: number
  recommendedLeverage: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface CompetingOffer {
  companyName: string
  tdsScore: number
  likelihood: 'HIGH' | 'MEDIUM' | 'LOW'
}

export interface CandidateProfilerResponse {
  tdsScore: number
  tdsPercentile: number
  tdsGrade: 'S' | 'A' | 'B' | 'C' | 'D'
  applicationDirection: ApplicationDirection
  salaryNegotiation: SalaryNegotiation
  competingOffers: CompetingOffer[]
  summary: string
}

export interface CandidateProfilerRequest {
  resumeText?: string
  currentCompany?: string
  yearsOfExperience?: number
  education?: string
  skills?: string[]
  targetSegment?: string
  targetCompanyId?: string
}
