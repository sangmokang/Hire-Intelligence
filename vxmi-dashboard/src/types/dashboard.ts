// ISO주차 타입 예: '2026-W12'
export type ISOWeek = string;

// S/D 매트릭스 아이템
export interface SDMatrixItem {
  segmentId: string;
  segmentName: string;
  demand: number;
  supply: number;
  sdRatio: number;
  otwPct: number;
  quadrant: 'OPPORTUNITY' | 'COMPETITIVE' | 'OVERSUPPLY' | 'NICHE';
  avgSalary: number | null;
  trend?: 'up' | 'down' | 'stable';
}

// 기업 채용 순위
export interface CompanyRankItem {
  companyId: string;
  rank: number;
  company: string;
  segment: string;
  weeklyCount: number;
  positions: string[];
  weekOverWeekChange: number;
}

// 기업 타임라인 데이터 포인트
export interface TimelineDataPoint {
  week: ISOWeek;
  count: number;
}

export interface CompanyTimeline {
  companyId: string;
  company: string;
  data: TimelineDataPoint[];
}

// 채용 트렌드 데이터 포인트
export interface TrendDataPoint {
  week: ISOWeek;
  count: number;
}

export interface SegmentTrend {
  segmentId: string;
  segmentName: string;
  data: TrendDataPoint[];
}

// 이력서 매칭 입력
export interface ResumeMatchInput {
  resumeText: string;
  preferredSegments?: string[];
  minScore?: number;
  maxResults?: number;
}

export interface MatchResult {
  companyId: string;
  company: string;
  score: number;
  segment: string;
  matchReason: string;
  matchedSkills: string[];
  activePostings: number;
}

export interface ResumeMatchOutput {
  matches: MatchResult[];
  extractedKeywords: string[];
  processingTimeMs: number;
  matchEngine: 'KEYWORD' | 'SEMANTIC';
}

// S/D 세그먼트 기본 타입
export interface Segment {
  id: string;
  name: string;
  demand: number;
  supply: number;
  otwPct: number;
  color: string;
}

// 세그먼트 확장 타입 (WoW + 상위기업)
export interface EnrichedSegment extends Segment {
  demandWoW: number;
  supplyWoW: number;
  topCompanies: string[];
}

// 드릴다운 패널 아이템
export interface DrilldownItem {
  company: string;
  position?: string;
  count: number;
  change?: number;
}

// 인재 유입/유출 흐름
export interface TalentFlowEntry {
  company: string;
  count: number;
}

export interface TalentFlow {
  inflow: TalentFlowEntry[];
  outflow: TalentFlowEntry[];
  totalInflow?: number;
  totalOutflow?: number;
  netChange?: number;
}

// 타임라인 필터 타입
export type TimelineMode = 'total' | 'keyword' | 'compound';
export type TimelineWeeks = 4 | 8 | 12 | 24;
export type TimelineTopN = 10 | 20 | 30;
export type KeywordOperator = 'AND' | 'OR';

// S/D 매트릭스 드릴다운 응답
export interface SDMatrixDrilldownCompany {
  company: string;
  count: number;
  rank?: number;
}

export interface SDMatrixDrilldownTrendPoint {
  week: ISOWeek;
  demand: number;
  supply: number;
}

export interface SDMatrixDrilldown {
  segmentId: string;
  segmentName: string;
  week: string;
  demand: number;
  supply: number;
  sdRatio: number;
  otwPct: number;
  avgSalary: number | null;
  topCompanies: SDMatrixDrilldownCompany[];
  weeklyTrend: SDMatrixDrilldownTrendPoint[];
}

// 기업 분석 프로필
export interface CompanyProfile {
  companyId: string;
  name: string;
  talentDensity: {
    overall: number;
    techDiversity: number;
    seniorRatio: number;
    avgTenure: string;
    internalOtwPct: number;
  };
  hiringPower: {
    overall: number;
    activePostings: number;
    weeklyTrend: number[];
  };
  talentFlow?: TalentFlow;
}
