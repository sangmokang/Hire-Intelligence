import type { Segment } from '../types'

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

/** 크롤러 표준 세그먼트 ID → FE 세그먼트 ID 매핑 */
export const CANONICAL_TO_FE: Record<string, string> = {
  dev_server:   'sw',
  dev_frontend: 'sw',
  dev_devops:   'sw',
  dev_mlai:     'data',
  dev_java:     'sw',
  dev_cto:      'sw',
  dev_total:    'sw',
  design:       'ux',
  pm_po:        'prod',
  marketing:    'mktg',
  hr:           'hr',
  cfo_finance:  'fin',
  sales:        'sales',
  strategy:     'prod',
}

/** 크롤러에서 사용하는 전체 표준 세그먼트 ID 목록 */
export const CRAWLER_SEGMENTS = [
  'dev_server', 'dev_frontend', 'dev_devops', 'dev_mlai', 'dev_java',
  'dev_cto', 'dev_total', 'design', 'pm_po', 'marketing', 'hr',
  'cfo_finance', 'sales', 'strategy',
] as const

