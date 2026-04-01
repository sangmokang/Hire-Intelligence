import { http, HttpResponse, delay } from 'msw';
import type { SDMatrixItem, CompanyRankItem, CompanyTimeline, SegmentTrend, ResumeMatchInput, ResumeMatchOutput } from '../../types/dashboard';

// 한국 IT 직군 세그먼트 목 데이터
const MOCK_SEGMENTS: SDMatrixItem[] = [
  {
    segmentId: 'seg-001',
    segmentName: '백엔드 엔지니어',
    demand: 3240,
    supply: 1820,
    sdRatio: 1.78,
    otwPct: 0.42,
    quadrant: 'OPPORTUNITY',
    avgSalary: null,
  },
  {
    segmentId: 'seg-002',
    segmentName: '프론트엔드 엔지니어',
    demand: 2100,
    supply: 2350,
    sdRatio: 0.89,
    otwPct: 0.31,
    quadrant: 'OVERSUPPLY',
    avgSalary: null,
  },
  {
    segmentId: 'seg-003',
    segmentName: 'AI/ML 엔지니어',
    demand: 1850,
    supply: 620,
    sdRatio: 2.98,
    otwPct: 0.67,
    quadrant: 'OPPORTUNITY',
    avgSalary: null,
  },
  {
    segmentId: 'seg-004',
    segmentName: 'DevOps/인프라',
    demand: 980,
    supply: 870,
    sdRatio: 1.13,
    otwPct: 0.38,
    quadrant: 'COMPETITIVE',
    avgSalary: null,
  },
  {
    segmentId: 'seg-005',
    segmentName: '데이터 엔지니어',
    demand: 1420,
    supply: 590,
    sdRatio: 2.41,
    otwPct: 0.55,
    quadrant: 'OPPORTUNITY',
    avgSalary: null,
  },
  {
    segmentId: 'seg-006',
    segmentName: 'iOS 개발자',
    demand: 480,
    supply: 510,
    sdRatio: 0.94,
    otwPct: 0.28,
    quadrant: 'NICHE',
    avgSalary: null,
  },
  {
    segmentId: 'seg-007',
    segmentName: 'Android 개발자',
    demand: 520,
    supply: 490,
    sdRatio: 1.06,
    otwPct: 0.29,
    quadrant: 'COMPETITIVE',
    avgSalary: null,
  },
  {
    segmentId: 'seg-008',
    segmentName: '보안 엔지니어',
    demand: 640,
    supply: 220,
    sdRatio: 2.91,
    otwPct: 0.61,
    quadrant: 'OPPORTUNITY',
    avgSalary: null,
  },
];

// 기업 채용 순위 목 데이터
const MOCK_COMPANY_RANKS: CompanyRankItem[] = [
  {
    companyId: 'co-001',
    rank: 1,
    company: '카카오',
    segment: 'AI/ML 엔지니어',
    weeklyCount: 142,
    positions: ['ML엔지니어', '리서치엔지니어', 'LLM엔지니어'],
    weekOverWeekChange: 18,
  },
  {
    companyId: 'co-002',
    rank: 2,
    company: '네이버',
    segment: '백엔드 엔지니어',
    weeklyCount: 138,
    positions: ['백엔드개발자', 'Java개발자', 'Kotlin개발자'],
    weekOverWeekChange: 5,
  },
  {
    companyId: 'co-003',
    rank: 3,
    company: '삼성SDS',
    segment: '데이터 엔지니어',
    weeklyCount: 127,
    positions: ['데이터엔지니어', '빅데이터플랫폼', 'Spark개발자'],
    weekOverWeekChange: -3,
  },
  {
    companyId: 'co-004',
    rank: 4,
    company: '쿠팡',
    segment: '백엔드 엔지니어',
    weeklyCount: 119,
    positions: ['SWE', '백엔드개발자', '플랫폼엔지니어'],
    weekOverWeekChange: 22,
  },
  {
    companyId: 'co-005',
    rank: 5,
    company: 'SK텔레콤',
    segment: 'AI/ML 엔지니어',
    weeklyCount: 98,
    positions: ['AI연구원', 'MLOps엔지니어', 'NLP엔지니어'],
    weekOverWeekChange: 11,
  },
  {
    companyId: 'co-006',
    rank: 6,
    company: 'LG CNS',
    segment: 'DevOps/인프라',
    weeklyCount: 87,
    positions: ['DevOps엔지니어', 'SRE', '클라우드엔지니어'],
    weekOverWeekChange: -1,
  },
  {
    companyId: 'co-007',
    rank: 7,
    company: '현대자동차',
    segment: '보안 엔지니어',
    weeklyCount: 76,
    positions: ['보안엔지니어', 'V2X보안', '클라우드보안'],
    weekOverWeekChange: 9,
  },
  {
    companyId: 'co-008',
    rank: 8,
    company: '토스',
    segment: '프론트엔드 엔지니어',
    weeklyCount: 71,
    positions: ['프론트엔드개발자', 'React개발자', '모바일웹'],
    weekOverWeekChange: -7,
  },
  {
    companyId: 'co-009',
    rank: 9,
    company: '라인플러스',
    segment: '백엔드 엔지니어',
    weeklyCount: 65,
    positions: ['서버개발자', '메시징플랫폼', 'Java개발자'],
    weekOverWeekChange: 2,
  },
  {
    companyId: 'co-010',
    rank: 10,
    company: '당근마켓',
    segment: 'AI/ML 엔지니어',
    weeklyCount: 58,
    positions: ['추천시스템', 'ML엔지니어', '검색엔지니어'],
    weekOverWeekChange: 14,
  },
];

// 타임라인 주차 생성 헬퍼 (최근 12주)
function generateWeeks(n: number): string[] {
  const weeks: string[] = [];
  const now = new Date('2026-03-24');
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i * 7);
    const year = d.getFullYear();
    const startOfYear = new Date(year, 0, 1);
    const week = Math.ceil(((d.getTime() - startOfYear.getTime()) / 86400000 + startOfYear.getDay() + 1) / 7);
    weeks.push(`${year}-W${String(week).padStart(2, '0')}`);
  }
  return weeks;
}

// 기업 타임라인 목 데이터
function generateTimeline(companyId: string, baseCount: number): CompanyTimeline {
  const company = MOCK_COMPANY_RANKS.find(c => c.companyId === companyId);
  const weeks = generateWeeks(12);
  return {
    companyId,
    company: company?.company ?? companyId,
    data: weeks.map((week, i) => ({
      week,
      count: Math.max(0, baseCount + Math.round((Math.random() - 0.4) * 20) + i * 2),
    })),
  };
}

// 세그먼트 트렌드 목 데이터
const MOCK_TRENDS: SegmentTrend[] = MOCK_SEGMENTS.slice(0, 5).map(seg => ({
  segmentId: seg.segmentId,
  segmentName: seg.segmentName,
  data: generateWeeks(12).map((week, i) => ({
    week,
    count: Math.max(0, seg.demand + Math.round((Math.random() - 0.4) * 200) + i * 15),
  })),
}));

export const dashboardHandlers = [
  // S/D 매트릭스 조회
  http.get('/api/v1/dashboard/sd-matrix', async ({ request }) => {
    await delay(200);
    const url = new URL(request.url);
    const week = url.searchParams.get('week');

    // week 파라미터 유효성 확인 (선택적)
    if (week && !/^\d{4}-W\d{2}$/.test(week)) {
      return HttpResponse.json(
        {
          type: 'https://vxmi.io/errors/validation',
          title: 'Validation Error',
          status: 400,
          detail: 'week 파라미터 형식이 올바르지 않습니다. 예: 2026-W12',
        },
        { status: 400 }
      );
    }

    const opportunitySegments = MOCK_SEGMENTS.filter(s => s.quadrant === 'OPPORTUNITY');
    const avgSDRatio = MOCK_SEGMENTS.reduce((sum, s) => sum + s.sdRatio, 0) / MOCK_SEGMENTS.length;
    const topOpportunity = MOCK_SEGMENTS
      .filter(s => s.quadrant === 'OPPORTUNITY')
      .sort((a, b) => b.sdRatio - a.sdRatio)[0];

    return HttpResponse.json({
      status: 'success',
      data: {
        summary: {
          totalPostings: MOCK_SEGMENTS.reduce((sum, s) => sum + s.demand, 0),
          opportunitySegments: opportunitySegments.length,
          avgSDRatio: Math.round(avgSDRatio * 100) / 100,
          topOpportunitySegment: topOpportunity?.segmentName ?? '',
        },
        segments: MOCK_SEGMENTS,
      },
    });
  }),

  // 기업 채용 순위 조회
  http.get('/api/v1/dashboard/companies', async ({ request }) => {
    await delay(250);
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') ?? '1', 10);
    const limit = parseInt(url.searchParams.get('limit') ?? '10', 10);
    const segmentId = url.searchParams.get('segmentId');

    let filtered = MOCK_COMPANY_RANKS;
    if (segmentId) {
      const seg = MOCK_SEGMENTS.find(s => s.segmentId === segmentId);
      if (seg) {
        filtered = MOCK_COMPANY_RANKS.filter(c => c.segment === seg.segmentName);
      }
    }

    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);

    return HttpResponse.json({
      status: 'success',
      data: paginated,
      pagination: {
        page,
        limit,
        totalItems: filtered.length,
        totalPages: Math.ceil(filtered.length / limit),
      },
    });
  }),

  // 기업 채용 타임라인 조회
  http.get('/api/v1/dashboard/timeline', async ({ request }) => {
    await delay(300);
    const url = new URL(request.url);
    const companyIds = url.searchParams.getAll('companyId');
    const weeksParam = parseInt(url.searchParams.get('weeks') ?? '12', 10);

    // 유효한 weeks 값 검증
    const validWeeks = [4, 8, 12, 26, 52];
    const weeks = validWeeks.includes(weeksParam) ? weeksParam : 12;

    const targetIds = companyIds.length > 0
      ? companyIds
      : MOCK_COMPANY_RANKS.slice(0, 5).map(c => c.companyId);

    const timelines = targetIds.map((id, i) =>
      generateTimeline(id, 80 + i * 10)
    );

    // weeks에 맞게 데이터 슬라이싱
    const sliced = timelines.map(t => ({
      ...t,
      data: t.data.slice(-weeks),
    }));

    return HttpResponse.json({
      status: 'success',
      data: sliced,
    });
  }),

  // 채용 트렌드 조회
  http.get('/api/v1/dashboard/trends', async ({ request }) => {
    await delay(200);
    const url = new URL(request.url);
    const segmentIds = url.searchParams.getAll('segmentId');

    const result = segmentIds.length > 0
      ? MOCK_TRENDS.filter(t => segmentIds.includes(t.segmentId))
      : MOCK_TRENDS;

    return HttpResponse.json({
      status: 'success',
      data: result,
    });
  }),

  // 이력서 매칭 (POST)
  http.post('/api/v1/dashboard/resume-match', async ({ request }) => {
    await delay(800); // 처리 시간 시뮬레이션
    const body = await request.json() as ResumeMatchInput;

    if (!body.resumeText || body.resumeText.trim().length < 10) {
      return HttpResponse.json(
        {
          type: 'https://vxmi.io/errors/validation',
          title: 'Validation Error',
          status: 400,
          detail: '이력서 텍스트가 너무 짧습니다. 최소 10자 이상 입력해주세요.',
        },
        { status: 400 }
      );
    }

    // 키워드 추출 시뮬레이션
    const keywords = ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS', 'Redis'];
    const minScore = body.minScore ?? 0.6;
    const maxResults = body.maxResults ?? 10;

    const mockMatches: ResumeMatchOutput = {
      matches: MOCK_COMPANY_RANKS.slice(0, maxResults).map((c, i) => ({
        companyId: c.companyId,
        company: c.company,
        score: Math.max(minScore, 0.95 - i * 0.06),
        segment: c.segment,
        matchReason: `${c.positions[0]} 포지션과 ${keywords.slice(0, 3).join(', ')} 스킬 매칭`,
        matchedSkills: keywords.slice(0, Math.max(2, 5 - i)),
        activePostings: c.weeklyCount,
      })).filter(m => m.score >= minScore),
      extractedKeywords: keywords,
      processingTimeMs: 823,
      matchEngine: 'KEYWORD',
    };

    return HttpResponse.json({
      status: 'success',
      data: mockMatches,
    }, { status: 200 });
  }),
];
