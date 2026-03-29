/** JD 인사이트 API 응답 타입 */

export interface TechTrend {
  name: string
  count: number
  previousCount: number
  change: number
}

export interface ExperienceDistribution {
  level: string
  count: number
  percentage: number
}

export interface SalaryBenchmark {
  segmentId: string
  segmentName: string
  salaryMin: number | null
  salaryMax: number | null
  salaryAvg: number | null
  sampleCount: number
}

export interface DomainTag {
  name: string
  count: number
}

export interface JdInsightsResponse {
  techTrends: TechTrend[]
  experienceDistribution: ExperienceDistribution[]
  salaryBenchmarks: SalaryBenchmark[]
  topDomainTags: DomainTag[]
  totalAnalyzed: number
}
