import type { Segment, EnrichedSegment } from '../types'

export const SEGMENTS: Segment[] = [
  { id: 'sw',    name: 'SW엔지니어링',  demand: 2840, supply: 18500, otwPct: 15, color: '#378ADD' },
  { id: 'data',  name: 'Data/AI',      demand: 1620, supply: 8200,  otwPct: 22, color: '#1D9E75' },
  { id: 'sales', name: '영업',          demand: 1240, supply: 15600, otwPct: 8,  color: '#E24B4A' },
  { id: 'prod',  name: 'Product',      demand: 890,  supply: 6100,  otwPct: 19, color: '#D4537E' },
  { id: 'ops',   name: '운영',          demand: 940,  supply: 11200, otwPct: 11, color: '#888780' },
  { id: 'mfg',   name: '제조',          demand: 1180, supply: 13600, otwPct: 9,  color: '#BA7517' },
  { id: 'mktg',  name: '마케팅',        demand: 760,  supply: 12400, otwPct: 13, color: '#7F77DD' },
  { id: 'fin',   name: '재무',          demand: 580,  supply: 9800,  otwPct: 10, color: '#5DCAA5' },
  { id: 'hr',    name: 'HR',           demand: 420,  supply: 7200,  otwPct: 14, color: '#F0997B' },
  { id: 'ux',    name: 'UX/UI',        demand: 680,  supply: 4800,  otwPct: 28, color: '#D85A30' },
  { id: 'legal', name: '법무',          demand: 280,  supply: 3200,  otwPct: 17, color: '#97C459' },
  { id: 'scm',   name: '물류SCM',       demand: 560,  supply: 8900,  otwPct: 12, color: '#FAC775' },
  { id: 'rd',    name: '연구개발',       demand: 840,  supply: 7400,  otwPct: 16, color: '#93B1EB' },
  { id: 'med',   name: '의료헬스케어',   demand: 720,  supply: 5600,  otwPct: 24, color: '#ED93B1' },
]

export const SEG_COLORS: Record<string, { bg: string; text: string }> = {
  'SW엔지니어링': { bg: '#E6F1FB', text: '#185FA5' },
  'Product':      { bg: '#FBEAF0', text: '#993556' },
  '제조':          { bg: '#FAEEDA', text: '#854F0B' },
  '재무':          { bg: '#E1F5EE', text: '#0F6E56' },
  '운영':          { bg: '#F1EFE8', text: '#5F5E5A' },
  '연구개발':       { bg: '#E6F1FB', text: '#185FA5' },
  'Data/AI':      { bg: '#E1F5EE', text: '#0F6E56' },
  '영업':          { bg: '#FCEBEB', text: '#A32D2D' },
  '마케팅':        { bg: '#EEEDFE', text: '#3C3489' },
}

export const SEG_OPTIONS = ['전체', 'SW엔지니어링', 'Data/AI', '영업', 'Product', '운영', '제조', '마케팅', '재무', 'HR', 'UX/UI', '법무', '물류SCM', '연구개발', '의료헬스케어']

export const SUGGESTED_KEYWORDS = ['Python', 'Java', 'Kotlin', 'React', 'Spring Boot', 'AWS', 'MSA', 'MLOps', 'DevOps', 'Kubernetes', '영업 관리', 'B2B 영업', '결제', 'HR', 'PMO']

const SEGMENT_ENRICHMENT: Record<string, { demandWoW: number; supplyWoW: number; topCompanies: string[] }> = {
  sw:    { demandWoW: 8.2,  supplyWoW: 1.3,  topCompanies: ['삼성전자', '네이버', 'LG CNS'] },
  data:  { demandWoW: 12.5, supplyWoW: 3.1,  topCompanies: ['카카오', 'SK텔레콤', '네이버'] },
  sales: { demandWoW: -3.1, supplyWoW: 0.8,  topCompanies: ['삼성물산', 'LG전자', '현대자동차'] },
  prod:  { demandWoW: 5.7,  supplyWoW: 2.4,  topCompanies: ['쿠팡', '토스', '당근'] },
  ops:   { demandWoW: -1.5, supplyWoW: 0.4,  topCompanies: ['CJ대한통운', '쿠팡', '삼성SDS'] },
  mfg:   { demandWoW: 2.3,  supplyWoW: -0.7, topCompanies: ['삼성전자', '현대자동차', 'SK하이닉스'] },
  mktg:  { demandWoW: -5.8, supplyWoW: 1.1,  topCompanies: ['카카오', '네이버', 'CJ ENM'] },
  fin:   { demandWoW: 4.1,  supplyWoW: 0.6,  topCompanies: ['삼성증권', 'KB국민은행', '하나금융'] },
  hr:    { demandWoW: 15.3, supplyWoW: 2.8,  topCompanies: ['삼성전자', 'LG전자', 'SK하이닉스'] },
  ux:    { demandWoW: 7.4,  supplyWoW: 4.2,  topCompanies: ['토스', '카카오', '네이버'] },
  legal: { demandWoW: -2.0, supplyWoW: 0.3,  topCompanies: ['삼성전자', 'SK그룹', 'LG전자'] },
  scm:   { demandWoW: 3.6,  supplyWoW: -1.2, topCompanies: ['CJ대한통운', '쿠팡', '롯데글로벌로지스'] },
  rd:    { demandWoW: 6.9,  supplyWoW: 1.8,  topCompanies: ['삼성전자', 'LG에너지솔루션', 'SK하이닉스'] },
  med:   { demandWoW: 18.2, supplyWoW: 5.5,  topCompanies: ['삼성바이오로직스', '셀트리온', '유한양행'] },
}

export function enrichSegments(segments: Segment[]): EnrichedSegment[] {
  return segments.map((s) => ({
    ...s,
    ...(SEGMENT_ENRICHMENT[s.id] ?? { demandWoW: 0, supplyWoW: 0, topCompanies: [] }),
  }))
}
