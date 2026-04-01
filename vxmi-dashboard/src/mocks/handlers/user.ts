import { http, HttpResponse, delay } from 'msw';
import type { UsageStats, NotificationPreferences, BillingHistoryItem } from '../../services/userService';

// 최근 30일 일별 사용량 목 데이터 생성
function generateDailyStats(): { date: string; count: number }[] {
  const stats: { date: string; count: number }[] = [];
  const now = new Date('2026-04-01');
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    stats.push({
      date: d.toISOString().split('T')[0] ?? '',
      count: Math.floor(Math.random() * 30) + 5,
    });
  }
  return stats;
}

const MOCK_USAGE_STATS: UsageStats = {
  totalApiCalls: 1842,
  currentMonthCalls: 247,
  dailyStats: generateDailyStats(),
  viewStats: [
    { view: '상위 기업 분석', count: 89 },
    { view: 'SD 매트릭스', count: 54 },
    { view: '이력서 매칭', count: 43 },
    { view: '채용 트렌드', count: 31 },
    { view: '기업 타임라인', count: 18 },
    { view: '기업 DNA', count: 12 },
  ],
};

let MOCK_NOTIFICATIONS: NotificationPreferences = {
  weeklyReport: true,
  hiringAlert: false,
  productUpdates: true,
};

const MOCK_BILLING_HISTORY: BillingHistoryItem[] = [
  { id: 'inv-001', date: '2026-03-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-002', date: '2026-02-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-003', date: '2026-01-01', amount: 49000, plan: 'Pro', status: '완료' },
  { id: 'inv-004', date: '2025-12-01', amount: 0, plan: 'Starter', status: '무료' },
];

export const userHandlers = [
  // 사용량 통계 조회
  http.get('/api/v1/me/usage', async () => {
    await delay(300);
    return HttpResponse.json({ status: 'success', data: MOCK_USAGE_STATS });
  }),

  // 알림 설정 조회
  http.get('/api/v1/me/notifications', async () => {
    await delay(200);
    return HttpResponse.json({ status: 'success', data: MOCK_NOTIFICATIONS });
  }),

  // 알림 설정 변경
  http.patch('/api/v1/me/notifications', async ({ request }) => {
    await delay(200);
    const body = await request.json() as Partial<NotificationPreferences>;
    MOCK_NOTIFICATIONS = { ...MOCK_NOTIFICATIONS, ...body };
    return HttpResponse.json({ status: 'success', data: MOCK_NOTIFICATIONS });
  }),

  // 계정 삭제
  http.delete('/api/v1/me', async () => {
    await delay(400);
    return HttpResponse.json({ status: 'success', message: '계정이 성공적으로 삭제되었습니다.' });
  }),

  // 결제 이력 조회
  http.get('/api/v1/me/billing/history', async () => {
    await delay(250);
    return HttpResponse.json({ status: 'success', data: MOCK_BILLING_HISTORY });
  }),

  // 리포트 미리보기
  http.get('/api/v1/me/report/preview', async () => {
    await delay(200);
    return HttpResponse.json({
      status: 'success',
      data: {
        html: '<h2>리포트 미리보기</h2><p>리포트 기능은 준비 중입니다.</p>',
      },
    });
  }),
];
