import { SEGMENTS } from './segments'

export const KEYWORD_CATEGORY_MAP: Record<string, string[]> = {
  // Tech
  '백엔드': ['sw', 'data', 'rd'],
  '프론트엔드': ['sw', 'ux', 'prod'],
  '풀스택': ['sw', 'data', 'ux'],
  '개발자': ['sw', 'data', 'rd', 'ux'],
  '엔지니어': ['sw', 'data', 'rd', 'mfg'],
  '소프트웨어': ['sw', 'data', 'rd'],
  'AI': ['data', 'sw', 'rd'],
  '머신러닝': ['data', 'sw', 'rd'],
  '데이터': ['data', 'sw', 'fin'],
  '데이터분석': ['data', 'fin', 'mktg'],
  '클라우드': ['sw', 'data'],
  'DevOps': ['sw', 'data'],
  'QA': ['sw', 'prod'],
  '보안': ['sw', 'ops'],
  '인프라': ['sw', 'ops'],

  // Product & Design
  '기획': ['prod', 'mktg', 'ops'],
  '기획자': ['prod', 'mktg'],
  'PM': ['prod', 'sw'],
  'PO': ['prod', 'sw'],
  '프로덕트': ['prod', 'ux', 'sw'],
  '디자인': ['ux', 'prod', 'mktg'],
  'UX': ['ux', 'prod'],
  'UI': ['ux', 'prod', 'sw'],

  // Business
  '영업': ['sales', 'ops'],
  '세일즈': ['sales', 'ops'],
  'B2B': ['sales', 'mktg'],
  '사업개발': ['sales', 'prod', 'ops'],
  '마케팅': ['mktg', 'sales', 'prod'],
  '광고': ['mktg', 'sales'],
  '브랜드': ['mktg', 'prod'],
  '콘텐츠': ['mktg', 'prod'],
  'CRM': ['mktg', 'sales', 'data'],
  '퍼포먼스': ['mktg', 'data'],

  // Operations
  '운영': ['ops', 'sales', 'scm'],
  'CS': ['ops', 'sales'],
  '고객': ['ops', 'sales', 'mktg'],
  '물류': ['scm', 'ops'],
  'SCM': ['scm', 'ops', 'mfg'],
  '구매': ['scm', 'ops', 'mfg'],

  // Manufacturing & R&D
  '제조': ['mfg', 'rd', 'scm'],
  '생산': ['mfg', 'scm', 'ops'],
  '품질': ['mfg', 'rd'],
  '연구': ['rd', 'data', 'med'],
  'R&D': ['rd', 'sw', 'data'],
  '연구개발': ['rd', 'sw', 'data'],

  // Support functions
  '인사': ['hr', 'ops'],
  'HR': ['hr', 'ops'],
  '채용': ['hr'],
  '교육': ['hr', 'ops'],
  '재무': ['fin', 'ops'],
  '회계': ['fin'],
  '세무': ['fin', 'legal'],
  '법무': ['legal', 'fin'],
  '컴플라이언스': ['legal', 'fin'],

  // Healthcare
  '의료': ['med', 'rd'],
  '헬스케어': ['med', 'rd', 'data'],
  '바이오': ['med', 'rd'],
  '임상': ['med', 'rd'],
  '제약': ['med', 'rd', 'mfg'],
}

export function searchByKeyword(keyword: string): string[] {
  const lower = keyword.toLowerCase()
  const matchedSegIds = new Set<string>()

  // 1. Direct segment name match
  for (const seg of SEGMENTS) {
    if (seg.name.toLowerCase().includes(lower) || lower.includes(seg.name.toLowerCase())) {
      matchedSegIds.add(seg.id)
    }
  }

  // 2. Keyword map match (partial)
  for (const [key, segIds] of Object.entries(KEYWORD_CATEGORY_MAP)) {
    if (key.toLowerCase().includes(lower) || lower.includes(key.toLowerCase())) {
      segIds.forEach(id => matchedSegIds.add(id))
    }
  }

  return Array.from(matchedSegIds)
}
