// 시장 신호판 Mock 데이터
// 신호 기준: RED < 0.5, YELLOW 0.5~1.0, GREEN >= 1.0

export type SignalLevel = 'RED' | 'YELLOW' | 'GREEN'
export type Trend4w = 'UP' | 'DOWN' | 'FLAT'
export type PersonaType = 'INHOUSE_HR' | 'HEADHUNTER' | 'CHRO' | 'JOB_SEEKER'

// S/D Ratio 기준으로 신호 레벨 결정
export function getSignalLevel(ratio: number): SignalLevel {
  if (ratio < 0.5) return 'RED'
  if (ratio < 1.0) return 'YELLOW'
  return 'GREEN'
}

// 페르소나 × 신호 조합별 Action Text (PRD 7-C 정의)
export const ACTION_TEXT: Record<SignalLevel, Record<PersonaType, string>> = {
  RED: {
    INHOUSE_HR: '공급 부족 시장입니다. 파이프라인을 즉시 열고 후보자 응답률을 높이는 JD 리라이팅을 권장합니다.',
    HEADHUNTER: 'fee 협상 시 이 S/D 데이터를 클라이언트에게 제시하면 수임료 상향이 가능합니다.',
    CHRO: '헤드헌터 수임을 검토하세요. 직접 채용보다 성공 확률이 높습니다.',
    JOB_SEEKER: '지금이 이직 협상력 최대 구간입니다. 복수 오퍼를 병행하세요.',
  },
  YELLOW: {
    INHOUSE_HR: '수급 균형 구간입니다. 고용 브랜딩과 JD 품질을 높여 경쟁 우위를 확보하세요.',
    HEADHUNTER: '경쟁이 치열한 구간입니다. 후보자 품질 차별화로 클라이언트 신뢰를 높이세요.',
    CHRO: '시장이 균형점에 있습니다. 내부 육성과 외부 채용을 병행하는 전략이 유효합니다.',
    JOB_SEEKER: '적정 경쟁 구간입니다. 차별화된 포트폴리오와 빠른 지원이 중요합니다.',
  },
  GREEN: {
    INHOUSE_HR: '후보자 공급이 충분합니다. 면접 절차를 강화하고 컬처핏 검증에 집중하세요.',
    HEADHUNTER: '공급 우위 시장입니다. 고품질 후보자 큐레이션으로 포지셔닝을 강화하세요.',
    CHRO: '인재 풀이 풍부한 시장입니다. 장기 파이프라인 구축과 리텐션 전략을 병행하세요.',
    JOB_SEEKER: '경쟁이 치열한 시장입니다. 업계 상위 10% 역량 증명에 집중하세요.',
  },
}

export interface MarketSignalSegment {
  id: string
  name: string
  ratio: number          // S/D Ratio
  signal: SignalLevel
  trend4w: Trend4w       // 4주 추세
  demand: number         // 채용 공고 수
  supply: number         // 인재 공급 수
  weeklyHistory: number[] // 12주 S/D Ratio 히스토리 (오래된 순)
}

// 14개 세그먼트 Mock 데이터
export const MARKET_SIGNALS: MarketSignalSegment[] = [
  {
    id: 'backend',
    name: '백엔드',
    ratio: 0.38,
    signal: 'RED',
    trend4w: 'DOWN',
    demand: 4820,
    supply: 1832,
    weeklyHistory: [0.55, 0.52, 0.49, 0.47, 0.46, 0.44, 0.42, 0.41, 0.40, 0.39, 0.38, 0.38],
  },
  {
    id: 'frontend',
    name: '프론트엔드',
    ratio: 0.62,
    signal: 'YELLOW',
    trend4w: 'FLAT',
    demand: 3210,
    supply: 1990,
    weeklyHistory: [0.70, 0.68, 0.65, 0.64, 0.63, 0.62, 0.61, 0.63, 0.64, 0.62, 0.61, 0.62],
  },
  {
    id: 'aiml',
    name: 'AI/ML',
    ratio: 0.21,
    signal: 'RED',
    trend4w: 'DOWN',
    demand: 6540,
    supply: 1373,
    weeklyHistory: [0.35, 0.33, 0.30, 0.28, 0.27, 0.25, 0.24, 0.23, 0.22, 0.21, 0.21, 0.21],
  },
  {
    id: 'data',
    name: '데이터',
    ratio: 0.45,
    signal: 'RED',
    trend4w: 'UP',
    demand: 3980,
    supply: 1791,
    weeklyHistory: [0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.43, 0.44, 0.44, 0.45, 0.45, 0.45],
  },
  {
    id: 'devops',
    name: 'DevOps',
    ratio: 0.31,
    signal: 'RED',
    trend4w: 'DOWN',
    demand: 2760,
    supply: 856,
    weeklyHistory: [0.42, 0.40, 0.38, 0.36, 0.35, 0.34, 0.33, 0.33, 0.32, 0.31, 0.31, 0.31],
  },
  {
    id: 'security',
    name: '보안',
    ratio: 0.18,
    signal: 'RED',
    trend4w: 'DOWN',
    demand: 1840,
    supply: 331,
    weeklyHistory: [0.25, 0.24, 0.23, 0.22, 0.21, 0.20, 0.20, 0.19, 0.19, 0.18, 0.18, 0.18],
  },
  {
    id: 'ios',
    name: 'iOS',
    ratio: 0.71,
    signal: 'YELLOW',
    trend4w: 'UP',
    demand: 980,
    supply: 696,
    weeklyHistory: [0.62, 0.63, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.70, 0.71, 0.71, 0.71],
  },
  {
    id: 'android',
    name: 'Android',
    ratio: 0.83,
    signal: 'YELLOW',
    trend4w: 'FLAT',
    demand: 870,
    supply: 722,
    weeklyHistory: [0.80, 0.81, 0.82, 0.82, 0.83, 0.83, 0.82, 0.83, 0.83, 0.83, 0.83, 0.83],
  },
  {
    id: 'qa',
    name: 'QA',
    ratio: 1.12,
    signal: 'GREEN',
    trend4w: 'UP',
    demand: 1120,
    supply: 1254,
    weeklyHistory: [0.95, 0.98, 1.00, 1.02, 1.04, 1.05, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12],
  },
  {
    id: 'pm',
    name: 'PM',
    ratio: 0.57,
    signal: 'YELLOW',
    trend4w: 'DOWN',
    demand: 2340,
    supply: 1334,
    weeklyHistory: [0.65, 0.64, 0.63, 0.61, 0.60, 0.59, 0.59, 0.58, 0.58, 0.57, 0.57, 0.57],
  },
  {
    id: 'design',
    name: '디자인',
    ratio: 1.34,
    signal: 'GREEN',
    trend4w: 'UP',
    demand: 1560,
    supply: 2090,
    weeklyHistory: [1.10, 1.14, 1.17, 1.19, 1.22, 1.24, 1.26, 1.28, 1.30, 1.31, 1.33, 1.34],
  },
  {
    id: 'marketing',
    name: '마케팅',
    ratio: 1.87,
    signal: 'GREEN',
    trend4w: 'UP',
    demand: 2180,
    supply: 4077,
    weeklyHistory: [1.60, 1.65, 1.68, 1.71, 1.74, 1.76, 1.78, 1.80, 1.82, 1.84, 1.86, 1.87],
  },
  {
    id: 'sales',
    name: '세일즈',
    ratio: 2.14,
    signal: 'GREEN',
    trend4w: 'FLAT',
    demand: 3400,
    supply: 7276,
    weeklyHistory: [2.10, 2.11, 2.12, 2.13, 2.13, 2.14, 2.14, 2.14, 2.13, 2.14, 2.14, 2.14],
  },
  {
    id: 'hr',
    name: 'HR',
    ratio: 1.05,
    signal: 'GREEN',
    trend4w: 'UP',
    demand: 890,
    supply: 935,
    weeklyHistory: [0.90, 0.93, 0.95, 0.96, 0.97, 0.98, 0.99, 1.00, 1.01, 1.02, 1.04, 1.05],
  },
]
