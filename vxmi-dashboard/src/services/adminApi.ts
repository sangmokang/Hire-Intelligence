import { apiClient } from './apiClient';

// 데이터 품질 모니터링
export interface WeeklyCollectionStats {
  week: string;
  totalPostings: number;
  totalCompanies: number;
  segmentsCovered: number;
  segmentsTotal: number;
}

export interface DataQualityResponse {
  currentWeek: string;
  weeklyStats: WeeklyCollectionStats[];
  missingSegments: string[];
  anomalies: Array<{
    week: string;
    prevWeek: string;
    prevTotalPostings: number;
    currTotalPostings: number;
    changePct: number;
  }>;
}

export interface CrawlStatusResponse {
  lastCrawlAt: string | null;
  lastCrawlStatus: string | null;
  totalCrawled: number;
  totalParsed: number;
  nextScheduled: string;
}

export const fetchDataQuality = async (): Promise<DataQualityResponse> => {
  const res = await apiClient.get('/admin/data-quality');
  return res.data.data;
};

export const fetchCrawlStatus = async (): Promise<CrawlStatusResponse> => {
  const res = await apiClient.get('/admin/crawl-status');
  return res.data.data;
};

// ── 유저 관리 ─────────────────────────────────────────────────────────────────

export interface AdminUserDetail {
  userId: string;
  email: string | null;
  name: string | null;
  role: string;
  plan: string;
  status: string;
  company: string | null;
  jobTitle: string | null;
  loginCount: number;
  lastLoginAt: string | null;
  createdAt: string | null;
  subscriptionPlan: string | null;
  subscriptionStatus: string | null;
  subscriptionStartedAt: string | null;
  subscriptionExpiresAt: string | null;
}

export interface AdminUserListResponse {
  users: AdminUserDetail[];
  total: number;
  offset: number;
  limit: number;
}

export interface AdminUserUpdateRequest {
  role?: string;
  status?: string;
  plan?: string;
}

export interface AdminUserListParams {
  offset?: number;
  limit?: number;
  role?: string;
  plan?: string;
  status?: string;
}

export const fetchAdminUsers = async (params?: AdminUserListParams): Promise<AdminUserListResponse> => {
  const res = await apiClient.get('/admin/users', { params });
  return res.data.data;
};

export const fetchAdminUserDetail = async (userId: string): Promise<AdminUserDetail> => {
  const res = await apiClient.get(`/admin/users/${userId}`);
  return res.data.data;
};

export const updateAdminUser = async (userId: string, data: AdminUserUpdateRequest): Promise<AdminUserDetail> => {
  const res = await apiClient.patch(`/admin/users/${userId}`, data);
  return res.data.data;
};

// ── 과금 관리 ─────────────────────────────────────────────────────────────────

export interface PlanStat {
  plan: string;
  count: number;
}

export interface BillingSummaryResponse {
  planStats: PlanStat[];
  totalUsers: number;
}

export interface PaymentItem {
  id: string;
  userId: string;
  userEmail: string | null;
  amount: number;
  plan: string;
  status: string;
  paidAt: string | null;
  createdAt: string | null;
}

export interface BillingPaymentsResponse {
  payments: PaymentItem[];
  total: number;
  offset: number;
  limit: number;
}

export const fetchBillingSummary = async (): Promise<BillingSummaryResponse> => {
  const res = await apiClient.get('/admin/billing/summary');
  return res.data.data;
};

export const fetchBillingPayments = async (params?: { offset?: number; limit?: number }): Promise<BillingPaymentsResponse> => {
  const res = await apiClient.get('/admin/billing/payments', { params });
  return res.data.data;
};
