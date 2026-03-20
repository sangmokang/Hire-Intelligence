import type { CompanyProfile } from '../types'

export const COMPANY_DB: Record<string, CompanyProfile> = {
  '토스': {
    name: '토스',
    talentDensity: { overall: 88, techDiversity: 91, seniorRatio: 78, avgTenure: '2.1년', internalOtwPct: 22 },
    hiringPower: { overall: 85, activePostings: 152, weeklyTrend: [88,96,104,112,124,118,130,138,144,148,152,152] },
    talentFlow: {
      inflow: [
        { company: '카카오', count: 47 },
        { company: '네이버', count: 38 },
        { company: '라인', count: 29 },
        { company: '쿠팡', count: 21 },
        { company: '당근마켓', count: 18 },
      ],
      outflow: [
        { company: '당근마켓', count: 31 },
        { company: '무신사', count: 24 },
        { company: '비바리퍼블리카', count: 19 },
        { company: '야놀자', count: 15 },
        { company: '번개장터', count: 11 },
      ],
      totalInflow: 153,
      totalOutflow: 100,
      netChange: 53,
    },
  },
  '카카오': {
    name: '카카오',
    talentDensity: { overall: 78, techDiversity: 85, seniorRatio: 72, avgTenure: '2.8년', internalOtwPct: 18 },
    hiringPower: { overall: 72, activePostings: 196, weeklyTrend: [168,174,180,188,190,194,196,200,198,196,196,196] },
    talentFlow: {
      inflow: [
        { company: '네이버', count: 52 },
        { company: '라인', count: 41 },
        { company: '삼성전자', count: 33 },
        { company: '쿠팡', count: 28 },
        { company: '하이퍼커넥트', count: 17 },
      ],
      outflow: [
        { company: '토스', count: 47 },
        { company: '당근마켓', count: 38 },
        { company: '라인', count: 30 },
        { company: '배달의민족', count: 26 },
        { company: '무신사', count: 19 },
      ],
      totalInflow: 171,
      totalOutflow: 160,
      netChange: 11,
    },
  },
  '네이버': {
    name: '네이버',
    talentDensity: { overall: 82, techDiversity: 88, seniorRatio: 80, avgTenure: '3.2년', internalOtwPct: 12 },
    hiringPower: { overall: 68, activePostings: 182, weeklyTrend: [190,188,186,188,184,182,180,178,182,182,182,182] },
    talentFlow: {
      inflow: [
        { company: '삼성전자', count: 44 },
        { company: '카카오', count: 39 },
        { company: '라인', count: 35 },
        { company: '쿠팡', count: 22 },
        { company: '리디', count: 14 },
      ],
      outflow: [
        { company: '카카오', count: 52 },
        { company: '토스', count: 38 },
        { company: '라인', count: 33 },
        { company: '당근마켓', count: 27 },
        { company: '오늘의집', count: 20 },
      ],
      totalInflow: 154,
      totalOutflow: 170,
      netChange: -16,
    },
  },
  '삼성전자': {
    name: '삼성전자',
    talentDensity: { overall: 95, techDiversity: 96, seniorRatio: 90, avgTenure: '5.8년', internalOtwPct: 8 },
    hiringPower: { overall: 55, activePostings: 248, weeklyTrend: [240,244,248,248,246,244,248,250,248,248,248,248] },
    talentFlow: {
      inflow: [
        { company: 'LG전자', count: 61 },
        { company: 'SK하이닉스', count: 48 },
        { company: '네이버', count: 27 },
        { company: '카카오', count: 19 },
        { company: '마이크론', count: 15 },
      ],
      outflow: [
        { company: '네이버', count: 44 },
        { company: '카카오', count: 33 },
        { company: '토스', count: 21 },
        { company: '쿠팡', count: 18 },
        { company: '당근마켓', count: 14 },
      ],
      totalInflow: 170,
      totalOutflow: 130,
      netChange: 40,
    },
  },
  '쿠팡': {
    name: '쿠팡',
    talentDensity: { overall: 71, techDiversity: 74, seniorRatio: 65, avgTenure: '1.9년', internalOtwPct: 31 },
    hiringPower: { overall: 79, activePostings: 144, weeklyTrend: [108,116,120,128,132,136,138,140,142,144,144,144] },
    talentFlow: {
      inflow: [
        { company: '배달의민족', count: 35 },
        { company: '마켓컬리', count: 28 },
        { company: '네이버', count: 22 },
        { company: '직방', count: 17 },
        { company: '야놀자', count: 13 },
      ],
      outflow: [
        { company: '당근마켓', count: 33 },
        { company: '카카오', count: 28 },
        { company: '배달의민족', count: 25 },
        { company: '토스', count: 21 },
        { company: '마켓컬리', count: 16 },
      ],
      totalInflow: 115,
      totalOutflow: 123,
      netChange: -8,
    },
  },
}

export const DEFAULT_COMPANY_BTNS = ['토스', '카카오', '네이버', '삼성전자', '쿠팡']
