// 액션 패널 관련 타입 정의

/** 액션 아이템 우선순위 */
export type ActionPriority = 'HIGH' | 'MEDIUM' | 'LOW';

/** 개별 행동 권고 아이템 */
export interface ActionItem {
  priority: ActionPriority;
  text: string;
  cta?: string;
  ctaUrl?: string;
}

/** 액션 패널 전체 데이터 (서버 응답 등에서 사용) */
export interface ActionPanelData {
  insight: string;
  actions: ActionItem[];
  relatedViews?: { label: string; path: string }[];
}
