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
}
