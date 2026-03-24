import { create } from 'zustand';

// 대시보드 필터 상태 정의
interface DashboardFilters {
  selectedWeek: string | null;      // ISOWeek 형식 e.g. '2026-W12'
  selectedSegments: string[];
  viewMode: 'supply' | 'demand';
  timelineMode: 'A' | 'B' | 'C';
  timelineWeeks: 4 | 8 | 12 | 26 | 52;
  timelineTopN: 20 | 50 | 100;
  timelineKeywords: string[];
  timelineOperator: 'AND' | 'OR';
}

interface DashboardState {
  filters: DashboardFilters;
  setFilter: <K extends keyof DashboardFilters>(key: K, value: DashboardFilters[K]) => void;
  resetFilters: () => void;
}

const DEFAULT_FILTERS: DashboardFilters = {
  selectedWeek: null,
  selectedSegments: [],
  viewMode: 'supply',
  timelineMode: 'A',
  timelineWeeks: 12,
  timelineTopN: 20,
  timelineKeywords: [],
  timelineOperator: 'AND',
};

export const useDashboardStore = create<DashboardState>((set) => ({
  filters: { ...DEFAULT_FILTERS },
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),
}));
