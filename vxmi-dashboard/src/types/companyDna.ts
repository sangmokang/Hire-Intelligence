export interface TechItem {
  name: string
  count: number
  pct: number
}

export interface TechDna {
  stackCount: number
  diversityIndex: number
  diversityScore: number
  topTechs: TechItem[]
}

export interface HiringDna {
  totalPostings: number
  growthVelocity: number | null
  growthLabel: string
  intensityScore: number
  roleDistribution: Record<string, number>
  segmentBreadth: number
}

export interface CompensationDna {
  salaryAvg: number | null
  salaryMin: number | null
  salaryMax: number | null
  positionPercentile: number | null
  positionLabel: string
  equityRatio: number
  benefitsCount: number
  topBenefits: string[]
}

export interface CultureSignals {
  growthStage: string | null
  newPositionRatio: number
  teamSizePatterns: string[]
  cultureScore: number
}

export interface CompanyDnaResponse {
  companyId: string
  companyName: string
  segmentId: string | null
  week: string
  overallScore: number
  tech: TechDna
  hiring: HiringDna
  compensation: CompensationDna
  culture: CultureSignals
}

export interface SegmentBenchmark {
  segmentId: string
  segmentName: string
  avgTechScore: number
  avgHiringScore: number
  avgSalary: number | null
  avgCultureScore: number
  companyCount: number
}
