import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../services/apiClient'
import { useAuthStore } from '../stores/authStore'
import type { ActionPanelProps } from '../components/common/ActionPanel'

interface ActionPanelContext {
  selectedSegment?: string
  currentData?: Record<string, unknown>
}

interface ActionPanelApiResponse {
  insight: string
  actions: Array<{
    priority: 'HIGH' | 'MEDIUM' | 'LOW'
    text: string
    cta?: string
    ctaUrl?: string
  }>
  relatedViews: Array<string | { label: string; path: string }>
  isAiGenerated: boolean
  locked?: boolean
}

// view slug → 한국어 레이블 매핑
const VIEW_LABELS: Record<string, string> = {
  'sd-matrix':           'S/D 매트릭스',
  'top-companies':       'Top 채용 기업',
  'timeline':            '채용 타임라인',
  'trends':              '채용 트렌드',
  'resume-match':        '이력서 매칭',
  'company-analysis':    '기업 분석',
  'market-signals':      '시장 신호판',
  'opp-alert':           'OppAlert 피드',
  'candidate-profiler':  '후보자 프로파일러',
  'company-dna':         '기업 DNA',
  'company-compare':     '기업 비교',
  'jd-insights':         'JD 인사이트',
}

// view별 기본 related views (API 실패 시 fallback)
const FALLBACK_RELATED_VIEWS: Record<string, { label: string; path: string }[]> = {
  'sd-matrix':          [{ label: '시장 신호판', path: '/dashboard/market-signals' }, { label: '채용 트렌드', path: '/dashboard/trends' }],
  'top-companies':      [{ label: '기업 분석', path: '/dashboard/company-analysis' }, { label: 'OppAlert', path: '/dashboard/opp-alert' }],
  'timeline':           [{ label: 'S/D 매트릭스', path: '/dashboard/sd-matrix' }, { label: '트렌드', path: '/dashboard/trends' }],
  'trends':             [{ label: 'S/D 매트릭스', path: '/dashboard/sd-matrix' }, { label: '타임라인', path: '/dashboard/timeline' }],
  'resume-match':       [{ label: '후보자 프로파일러', path: '/dashboard/candidate-profiler' }],
  'company-analysis':   [{ label: '기업 DNA', path: '/dashboard/company-dna' }, { label: 'OppAlert', path: '/dashboard/opp-alert' }],
  'market-signals':     [{ label: 'S/D 매트릭스', path: '/dashboard/sd-matrix' }, { label: 'OppAlert', path: '/dashboard/opp-alert' }],
  'opp-alert':          [{ label: '시장 신호판', path: '/dashboard/market-signals' }, { label: '기업 분석', path: '/dashboard/company-analysis' }],
  'candidate-profiler': [{ label: '이력서 매칭', path: '/dashboard/resume-match' }, { label: '시장 신호판', path: '/dashboard/market-signals' }],
}

export function useActionPanel(view: string, context?: ActionPanelContext): ActionPanelProps {
  const user = useAuthStore((s) => s.user)

  const body = useMemo(() => ({
    view,
    context: {
      ...context,
      userCategory: user?.category ?? 'INHOUSE_HR',
      userPlan: user?.plan ?? 'STARTER',
    },
  }), [view, context, user?.category, user?.plan])

  const { data, isLoading } = useQuery({
    queryKey: ['action-panel', view, body.context.userCategory, body.context.userPlan, context?.selectedSegment],
    queryFn: async () => {
      const res = await apiClient.post<{ status: string; data: ActionPanelApiResponse }>('/api/v1/action-panel', body)
      return res.data.data
    },
    staleTime: 1000 * 60 * 60, // 1시간
    retry: 1,
  })

  const isLocked = data?.locked ?? false
  const normalizedRelatedViews = data
    ? data.relatedViews.map((relatedView) => {
      if (typeof relatedView === 'string') {
        return {
          label: VIEW_LABELS[relatedView] ?? relatedView,
          path: `/dashboard/${relatedView}`,
        }
      }
      return relatedView
    })
    : (FALLBACK_RELATED_VIEWS[view] ?? [])

  return {
    insight: data?.insight ?? (isLoading ? '분석 중...' : '인사이트를 불러올 수 없습니다.'),
    actions: data?.actions ?? [],
    relatedViews: normalizedRelatedViews,
    isLocked,
  }
}
