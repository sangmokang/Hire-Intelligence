// 오프셋 기반 페이지네이션
export interface OffsetPagination {
  page: number;
  limit: number;
  totalItems: number;
  totalPages: number;
}

// 커서 기반 페이지네이션
export interface CursorPagination {
  cursor: string;
  nextCursor: string | null;
  hasMore: boolean;
  limit: number;
}

// API 응답 래퍼
export interface ApiResponse<T> {
  status: 'success';
  data: T;
}

export interface ApiListResponse<T> {
  status: 'success';
  data: T[];
  pagination: OffsetPagination | CursorPagination;
}

// RFC 7807 표준 에러 형식
export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

// 인증 응답
export interface AuthTokenResponse {
  accessToken: string;
  user: import('./auth').User;
}

// 대시보드 요약
export interface DashboardSummary {
  totalPostings: number;
  opportunitySegments: number;
  avgSDRatio: number;
  topOpportunitySegment: string;
}
