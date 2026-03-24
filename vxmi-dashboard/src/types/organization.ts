// 조직 타입
export type OrganizationType = 'SEARCH_FIRM' | 'CORPORATION' | 'INDIVIDUAL';

// 조직 내 역할
export type OrgRole = 'OWNER' | 'ADMIN' | 'MEMBER';

export interface Organization {
  id: string;
  name: string;
  type: OrganizationType;
  plan: import('./auth').BusinessPlan;
  billingEmail: string;
  maxSeats: number;
  activeSeats: number;
  settings: OrganizationSettings;
  createdAt: string;
  updatedAt: string;
}

export interface OrganizationSettings {
  allowedSegments: string[];
  dataRetentionWeeks: number;
  ssoEnabled: boolean;
  customBranding: boolean;
}

export interface OrganizationMember {
  id: string;
  organizationId: string;
  userId: string;
  orgRole: OrgRole;
  joinedAt: string;
}
