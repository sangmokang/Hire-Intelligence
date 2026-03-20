export interface Segment {
  id: string
  name: string
  demand: number
  supply: number
  otwPct: number
  color: string
}

export interface EnrichedSegment extends Segment {
  demandWoW: number
  supplyWoW: number
  topCompanies: string[]
}

export interface CompanyRankItem {
  rank: number
  company: string
  segment: string
  weeklyCount: number
  positions: string[]
  weekOverWeekChange: number
}

export interface TrendDataPoint {
  week: string
  weekLabel: string
  segmentId: string
  count: number
}

export interface MatchResult {
  company: string
  score: number
  segment: string
  matchReason: string
  matchedSkills: string[]
  activePostings: number
}

export interface TalentFlowCompany {
  company: string
  count: number
}

export interface TalentFlow {
  inflow: TalentFlowCompany[]
  outflow: TalentFlowCompany[]
  totalInflow: number
  totalOutflow: number
  netChange: number
}

export interface CompanyProfile {
  name: string
  talentDensity: {
    overall: number
    techDiversity: number
    seniorRatio: number
    avgTenure: string
    internalOtwPct: number
  }
  hiringPower: {
    overall: number
    activePostings: number
    weeklyTrend: number[]
  }
  talentFlow: TalentFlow
}

export interface DrilldownItem {
  company: string
  position: string
  count: number
}

export type TimelineMode = 'total' | 'keyword' | 'compound'
export type TimelineWeeks = 4 | 8 | 12 | 26 | 52
export type TimelineTopN = 20 | 50 | 100
export type KeywordOperator = 'AND' | 'OR'

export interface TimelineRankItem {
  rank: number
  company: string
  segment: string
  totalCount: number
  weeklySeries: number[]
  wowChange: number
  matchedKeywords?: string[]
}
