import { useState } from 'react'
import { useResumeMatch } from '../../hooks/useDashboard'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { ActionPanelLayout } from '../common/ActionPanelLayout'

const SAMPLE_RESUME = `Java, Kotlin, Spring Boot, Spring Batch, MSA, Kafka, Redis, MySQL, AWS (EKS, RDS, S3)
핀테크 도메인 5년 경력
대용량 트랜잭션 처리 시스템 설계 및 운영
결제/정산 시스템 개발 경험
팀 리드 경험 (5인 팀)`
import { EmptyState } from '../common/EmptyState'
import type { MatchResult } from '../../types/dashboard'

const SCORE_COLORS: Record<string, string> = {
  '토스': '#378ADD',
  '배달의민족': '#1D9E75',
  '당근마켓': '#D4537E',
  '카카오페이': '#BA7517',
}

const DEFAULT_SCORE_COLOR = '#888780'

export function ResumeMatchView() {
  const [resumeText, setResumeText] = useState('')
  const { mutate, data: response, isPending, error } = useResumeMatch()

  const results: MatchResult[] = response?.data?.matches ?? []

  const handleMatch = () => {
    if (!resumeText.trim()) return
    mutate({ resumeText })
  }

  // ActionPanel 데이터 — rule-based 인사이트 및 추천 액션
  const panelProps = {
    insight: '이력서 키워드 매칭으로 최적의 포지션-후보자 연결을 찾을 수 있습니다.',
    actions: [
      { priority: 'MEDIUM' as const, text: '매칭 점수 80점 이상 결과에 우선 집중하세요' },
      { priority: 'LOW' as const, text: '추출된 키워드로 JD를 최적화하세요' },
    ],
    relatedViews: [
      { label: '기업 분석', path: '/dashboard/company-analysis' },
      { label: 'Top 채용 볼륨', path: '/dashboard/top-companies' },
    ],
    isLocked: false,
  }

  return (
    <ActionPanelLayout panel={panelProps}>
    <ErrorBoundary>
      <div className="p-6">
        <h1 className="text-lg font-semibold text-gray-900 mb-1">이력서 매칭</h1>
        <p className="text-sm text-gray-500 mb-4">
          이력서 또는 주요 스킬을 붙여넣으세요
        </p>
        <textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          placeholder="예: Java, Kotlin, Spring Boot, MSA, AWS, 핀테크 경험 5년..."
          className="w-full min-h-[120px] text-sm p-3 border border-gray-200 rounded-xl bg-gray-100 text-gray-900 resize-y font-sans focus:outline-none focus:border-gray-400"
          rows={5}
        />
        <div className="flex gap-2 mt-3 mb-2">
          <button
            onClick={() => setResumeText(SAMPLE_RESUME)}
            className="px-4 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
          >
            샘플 입력
          </button>
          <button
            onClick={handleMatch}
            disabled={isPending || !resumeText.trim()}
            className="px-4 py-1.5 text-xs bg-gray-900 text-white rounded-md hover:opacity-85 transition-opacity disabled:opacity-40"
          >
            {isPending ? '분석 중...' : '관련 기업 매칭 →'}
          </button>
        </div>

        {error && (
          <p className="mt-2 text-xs text-red-500">
            매칭 중 오류가 발생했습니다: {(error as Error).message}
          </p>
        )}

        {response && results.length === 0 && (
          <EmptyState
            title="매칭 결과가 없습니다"
            description="입력한 스킬과 매칭되는 기업을 찾지 못했습니다."
          />
        )}

        {results.length > 0 && (
          <>
            {response?.data?.extractedKeywords && response.data.extractedKeywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-3 mt-1">
                <span className="text-xs text-gray-500 self-center">추출된 키워드:</span>
                {response.data.extractedKeywords.map((kw) => (
                  <span
                    key={kw}
                    className="text-xs px-2 py-0.5 bg-gray-100 border border-gray-200 rounded-md text-gray-600"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 mt-4">
              {results.map((r, i) => {
                const color = SCORE_COLORS[r.company] ?? DEFAULT_SCORE_COLOR
                return (
                  <div key={i} className="p-4 bg-gray-100 rounded-xl border border-gray-200">
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">{r.company}</span>
                      <span className="text-lg font-medium" style={{ color }}>{r.score}</span>
                    </div>
                    <div className="h-1 bg-gray-200 rounded mb-2 overflow-hidden">
                      <div
                        className="h-full rounded transition-all"
                        style={{ width: `${r.score}%`, background: color }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mb-1">{r.segment}</p>
                    <p className="text-xs text-gray-500 leading-relaxed mb-3">{r.matchReason}</p>
                    <div className="flex flex-wrap gap-1">
                      {r.matchedSkills.map((s, j) => (
                        <span
                          key={j}
                          className="text-xs px-2 py-0.5 bg-white border border-gray-200 rounded-md text-gray-500"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
    </ActionPanelLayout>
  )
}
