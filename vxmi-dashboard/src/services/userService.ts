import { apiClient } from './apiClient';

export interface NotificationPreferences {
  weeklyReport: boolean;
  hiringAlert: boolean;
  productUpdates: boolean;
}

export interface DailyUsageStat {
  date: string;
  count: number;
}

export interface ViewUsageStat {
  view: string;
  count: number;
}

export interface UsageStats {
  totalApiCalls: number;
  currentMonthCalls: number;
  dailyStats: DailyUsageStat[];
  viewStats: ViewUsageStat[];
}

export interface BillingHistoryItem {
  id: string;
  date: string;
  amount: number;
  plan: string;
  status: string;
}

// 사용량 통계 조회
export const fetchUsageStats = (): Promise<{ data: { status: string; data: UsageStats } }> =>
  apiClient.get('/api/v1/me/usage');

// 알림 설정 조회
export const fetchNotificationPrefs = (): Promise<{ data: { status: string; data: NotificationPreferences } }> =>
  apiClient.get('/api/v1/me/notifications');

// 알림 설정 변경
export const updateNotificationPrefs = (
  prefs: Partial<NotificationPreferences>
): Promise<{ data: { status: string; data: NotificationPreferences } }> =>
  apiClient.patch('/api/v1/me/notifications', prefs);

// 계정 삭제
export const deleteAccount = (currentPassword: string): Promise<{ data: { status: string; message: string } }> =>
  apiClient.delete('/api/v1/me', { data: { currentPassword } });

// 결제 이력 조회
export const fetchBillingHistory = (): Promise<{
  data: { status: string; data: BillingHistoryItem[] };
}> => apiClient.get('/api/v1/me/billing/history');
