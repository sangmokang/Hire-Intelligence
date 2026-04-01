import { authHandlers } from './auth';
// 대시보드 핸들러 비활성화 — 실제 백엔드 API 사용
// import { dashboardHandlers } from './dashboard';

export const handlers = [...authHandlers];
