import type { MatchResult } from '../types'

export const SAMPLE_RESUME = `Java, Kotlin, Spring Boot, Spring Batch, MSA, Kafka, Redis, MySQL, AWS (EKS, RDS, S3)
핀테크 도메인 5년 경력
대용량 트랜잭션 처리 시스템 설계 및 운영
결제/정산 시스템 개발 경험
팀 리드 경험 (5인 팀)`

export const MATCH_DB: MatchResult[] = [
  { company: '토스', score: 94, segment: '핀테크 SW', matchReason: '결제/정산 시스템 직접 매칭, Java/Kotlin 핵심 스택, 대용량 MSA 환경', matchedSkills: ['Kotlin', 'Spring Boot', 'Kafka', 'MSA', '결제'], activePostings: 152 },
  { company: '배달의민족', score: 91, segment: 'SW엔지니어링', matchReason: '대용량 트랜잭션 처리 경험, Spring 기반 백엔드 아키텍처 선호', matchedSkills: ['Java', 'Spring Batch', 'MySQL', 'AWS', '팀리드'], activePostings: 112 },
  { company: '당근마켓', score: 88, segment: 'SW엔지니어링', matchReason: 'MSA 전환 진행 중, 플랫폼 확장 단계에 리드 경험 높은 가치', matchedSkills: ['Kotlin', 'Redis', 'Spring Boot', 'EKS'], activePostings: 98 },
  { company: '카카오페이', score: 85, segment: '핀테크', matchReason: '금융/결제 인프라 강화 채용 중, Java 백엔드 + 정산 경험 최우선', matchedSkills: ['Java', 'MSA', '정산', '보안', 'RDS'], activePostings: 118 },
]

export const SCORE_COLORS: Record<string, string> = {
  '토스': '#378ADD',
  '배달의민족': '#1D9E75',
  '당근마켓': '#D4537E',
  '카카오페이': '#BA7517',
}
