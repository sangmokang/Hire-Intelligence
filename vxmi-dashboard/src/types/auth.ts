// 사용자 역할 - 계층적 RBAC
export type UserRole = 'SUPER_ADMIN' | 'USER' | 'GUEST';

// 사용자 카테고리 - PRD 2트랙 정의에 맞춤
export type UserCategory = 'JOB_SEEKER' | 'INHOUSE_HR' | 'HEADHUNTER' | 'CHRO';

// 사용자 상태
export type UserStatus = 'ACTIVE' | 'INACTIVE' | 'BLOCKED' | 'PENDING_DELETE' | 'DELETED';

// 플랜 타입 - 2트랙 5티어 구조
export type TalentPlan = 'TALENT_FREE' | 'TALENT_PLUS';
export type BusinessPlan = 'STARTER' | 'PRO' | 'ENTERPRISE';
export type PlanType = TalentPlan | BusinessPlan;

export interface User {
  id: string;
  email: string;
  name: string;
  profileImageUrl?: string;
  role: UserRole;
  category: UserCategory;
  plan: PlanType;
  track: 'TALENT' | 'BUSINESS'; // 트랙 구분 (신규)
  status: UserStatus;
  company?: string;
  phone?: string;
  jobTitle?: string;       // 직함 (신규)
  organizationId?: string; // 멀티테넌시 조직 ID (신규)
  authProvider: 'EMAIL' | 'GOOGLE';
  createdAt?: string;
  lastLoginAt?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  category: UserCategory;
  company?: string;
}

export interface AuthResponse {
  status: 'success' | 'error';
  data: {
    accessToken: string;
    refreshToken?: string;
    user: User;
  };
}

export interface ApiError {
  status: 'error';
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

// 권한 레벨 체크 헬퍼
export const ROLE_LEVEL: Record<UserRole, number> = {
  SUPER_ADMIN: 100,
  USER: 10,
  GUEST: 0,
};

export function hasPermission(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_LEVEL[userRole] >= ROLE_LEVEL[requiredRole];
}

// 카테고리별 기본 트랙 매핑
export function getDefaultTrack(category: UserCategory): 'TALENT' | 'BUSINESS' {
  if (category === 'JOB_SEEKER') return 'TALENT';
  return 'BUSINESS';
}
