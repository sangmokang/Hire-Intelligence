import type { Segment, EnrichedSegment } from '../types'

// Industry segments - companies grouped by industry domain
export const INDUSTRY_SEGMENTS: Segment[] = [
  { id: 'it-platform',   name: 'IT/플랫폼',       demand: 3200, supply: 22000, otwPct: 18, color: '#378ADD' },
  { id: 'fintech',       name: '핀테크/금융',      demand: 1850, supply: 14200, otwPct: 15, color: '#5DCAA5' },
  { id: 'semiconductor', name: '전자/반도체',       demand: 2680, supply: 19500, otwPct: 12, color: '#7F77DD' },
  { id: 'automotive',    name: '자동차/모빌리티',    demand: 1420, supply: 11800, otwPct: 10, color: '#E24B4A' },
  { id: 'ecommerce',     name: '커머스/유통',       demand: 1680, supply: 9600,  otwPct: 21, color: '#BA7517' },
  { id: 'game-ent',      name: '게임/엔터',         demand: 980,  supply: 7200,  otwPct: 16, color: '#D4537E' },
  { id: 'bio-health',    name: '바이오/헬스케어',    demand: 920,  supply: 5400,  otwPct: 26, color: '#ED93B1' },
  { id: 'telecom',       name: '통신/인프라',       demand: 1560, supply: 13400, otwPct: 11, color: '#93B1EB' },
  { id: 'logistics',     name: '물류/운송',         demand: 780,  supply: 8200,  otwPct: 13, color: '#FAC775' },
  { id: 'defense',       name: '방산/중공업',       demand: 640,  supply: 5800,  otwPct: 9,  color: '#888780' },
  { id: 'consulting',    name: '컨설팅/서비스',     demand: 520,  supply: 6400,  otwPct: 14, color: '#D85A30' },
  { id: 'energy',        name: '에너지/소재',       demand: 880,  supply: 7600,  otwPct: 8,  color: '#97C459' },
]

const INDUSTRY_ENRICHMENT: Record<string, { demandWoW: number; supplyWoW: number; topCompanies: string[] }> = {
  'it-platform':   { demandWoW: 9.4,   supplyWoW: 1.8,  topCompanies: ['카카오', '네이버', '당근'] },
  'fintech':       { demandWoW: 6.2,   supplyWoW: 2.1,  topCompanies: ['토스', '두나무', 'KB국민은행'] },
  'semiconductor': { demandWoW: 4.8,   supplyWoW: 0.9,  topCompanies: ['삼성전자', 'SK하이닉스', 'LG전자'] },
  'automotive':    { demandWoW: 2.1,   supplyWoW: -0.4, topCompanies: ['현대자동차', '현대모비스', 'KG모빌리티'] },
  'ecommerce':     { demandWoW: 7.3,   supplyWoW: 3.2,  topCompanies: ['쿠팡', '배달의민족', '마켓컬리'] },
  'game-ent':      { demandWoW: -2.5,  supplyWoW: 0.6,  topCompanies: ['크래프톤', '넥슨', 'CJ ENM'] },
  'bio-health':    { demandWoW: 15.6,  supplyWoW: 4.8,  topCompanies: ['삼성바이오로직스', '셀트리온', '유한양행'] },
  'telecom':       { demandWoW: 1.9,   supplyWoW: 0.3,  topCompanies: ['SK텔레콤', 'KT', 'LG U+'] },
  'logistics':     { demandWoW: 3.4,   supplyWoW: -0.8, topCompanies: ['CJ대한통운', '쿠팡로지스틱스', '롯데글로벌로지스'] },
  'defense':       { demandWoW: 5.1,   supplyWoW: 1.2,  topCompanies: ['한화시스템', 'LIG넥스원', '한국항공우주'] },
  'consulting':    { demandWoW: -1.3,  supplyWoW: 0.5,  topCompanies: ['맥킨지', 'BCG', '삼정KPMG'] },
  'energy':        { demandWoW: 8.7,   supplyWoW: 1.5,  topCompanies: ['LG에너지솔루션', 'SK이노베이션', '포스코'] },
}

export function enrichIndustrySegments(segments: Segment[]): EnrichedSegment[] {
  return segments.map((s) => ({
    ...s,
    ...(INDUSTRY_ENRICHMENT[s.id] ?? { demandWoW: 0, supplyWoW: 0, topCompanies: [] }),
  }))
}
