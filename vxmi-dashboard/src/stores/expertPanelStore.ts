/**
 * Expert Panel Zustand 상태 관리
 */
import { create } from 'zustand';
import type { ExpertResponseItem, QueryClassification, SessionSummary } from '../services/expertPanelApi';
import { askExpert, submitFeedback, getSessions } from '../services/expertPanelApi';

interface ExpertPanelState {
  // UI 상태
  isOpen: boolean;
  query: string;
  isLoading: boolean;

  // 응답 상태
  classification: QueryClassification | null;
  responses: ExpertResponseItem[];
  sessionId: string | null;
  error: string | null;

  // 히스토리
  history: SessionSummary[];

  // Actions
  toggle: () => void;
  close: () => void;
  setQuery: (query: string) => void;
  ask: (query: string, view?: string) => Promise<void>;
  sendFeedback: (expertType: string, feedbackType: 'HELPFUL' | 'NOT_HELPFUL', rating?: number) => Promise<void>;
  loadHistory: () => Promise<void>;
  reset: () => void;
}

export const useExpertPanelStore = create<ExpertPanelState>((set, get) => ({
  // 초기 상태
  isOpen: false,
  query: '',
  isLoading: false,
  classification: null,
  responses: [],
  sessionId: null,
  error: null,
  history: [],

  toggle: () => set((s) => ({ isOpen: !s.isOpen })),
  close: () => set({ isOpen: false }),
  setQuery: (query: string) => set({ query }),

  ask: async (query: string, view?: string) => {
    set({ isLoading: true, error: null, responses: [], classification: null, sessionId: null });
    try {
      const result = await askExpert({ query, view });
      set({
        classification: result.classification,
        responses: result.responses,
        sessionId: result.sessionId,
        isLoading: false,
        query: '',
      });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : '전문가 응답을 가져오는 중 오류가 발생했습니다.';
      set({ error: message, isLoading: false });
    }
  },

  sendFeedback: async (expertType: string, feedbackType: 'HELPFUL' | 'NOT_HELPFUL', rating?: number) => {
    const { sessionId } = get();
    if (!sessionId) return;
    try {
      await submitFeedback({ sessionId, expertType, feedbackType, rating });
    } catch {
      // 피드백 실패는 사용자에게 표시하지 않음
    }
  },

  loadHistory: async () => {
    try {
      const sessions = await getSessions();
      set({ history: sessions });
    } catch {
      // 히스토리 로드 실패는 무시
    }
  },

  reset: () => set({
    query: '',
    isLoading: false,
    classification: null,
    responses: [],
    sessionId: null,
    error: null,
  }),
}));
