import { useState } from 'react'
import { useCompanyAnalysis } from '../../hooks/useDashboard'
import { SparkBars } from '../common/SparkBars'

const DEFAULT_COMPANY_BTNS = ['토스', '카카오', '네이버', '삼성전자', '쿠팡']
import { TalentFlowChart } from '../common/TalentFlowChart'
import type { TalentFlow } from '../../types/dashboard'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'

export function CompanyAnalysisView() {
  const [selectedCompany, setSelectedCompany] = useState('토스')
  const [inputVal, setInputVal] = useState('')

  const { data: response, isLoading, error } = useCompanyAnalysis(selectedCompany)

  const profile = response?.data ?? null

  return (
    <ErrorBoundary>
      <div>
        {/* Quick-select buttons */}
        <div className="flex flex-wrap gap-2 mb-3">
          {DEFAULT_COMPANY_BTNS.map((c) => (
            <button
              key={c}
              onClick={() => setSelectedCompany(c)}
              className={`px-3 py-1.5 text-xs border rounded-md transition-colors ${
                selectedCompany === c
                  ? 'bg-gray-100 border-gray-200 text-gray-900 font-medium'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        {/* Free-text input */}
        <div className="flex gap-2 mb-5">
          <input
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && inputVal.trim()) setSelectedCompany(inputVal.trim()) }}
            placeholder="다른 기업 입력..."
            className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-100 text-gray-900 focus:outline-none focus:border-gray-400"
          />
          <button
            onClick={() => { if (inputVal.trim()) setSelectedCompany(inputVal.trim()) }}
            className="px-4 py-2 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
          >
            분석
          </button>
        </div>

        {isLoading && (
          <div className="grid grid-cols-2 gap-4">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        )}

        {error && (
          <p className="text-sm text-red-500">
            "{selectedCompany}" 데이터를 불러오는 중 오류가 발생했습니다.
          </p>
        )}

        {!isLoading && !error && !profile && (
          <EmptyState
            title={`"${selectedCompany}" 데이터 없음`}
            description="해당 기업의 분석 데이터를 찾을 수 없습니다."
          />
        )}

        {!isLoading && !error && profile && (
          <>
            <div className="grid grid-cols-2 gap-4">
              {/* Panel A: Talent Density */}
              <div className="p-4 bg-gray-100 rounded-xl border border-gray-200">
                <p className="text-xs text-gray-500 mb-2">인재 밀도 지수</p>
                <p className="text-3xl font-medium text-gray-900">
                  {profile.talentDensity.overall}
                  <span className="text-sm text-gray-500 font-normal">/100</span>
                </p>
              </div>

              {/* Panel B: Hiring Power */}
              <div className="p-4 bg-gray-100 rounded-xl border border-gray-200">
                <p className="text-xs text-gray-500 mb-2">채용 파워 지수</p>
                <p className="text-3xl font-medium text-gray-900 mb-4">
                  {profile.hiringPower.overall}
                  <span className="text-sm text-gray-500 font-normal">/100</span>
                </p>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-2xl font-medium text-gray-900">{profile.hiringPower.activePostings}</span>
                  <span className="text-xs text-gray-500">현재 활성 포지션</span>
                </div>
                <p className="text-xs text-gray-500 mb-2">12주 채용 추이</p>
                <SparkBars data={profile.hiringPower.weeklyTrend} />
                <p className="text-xs text-gray-500 mt-1">10/7 → 12/23 · 빨간 막대: 최근</p>
              </div>
            </div>

            {/* Talent Flow section — only if talentFlow exists on profile */}
            {'talentFlow' in profile && (profile as unknown as Record<string, unknown>).talentFlow && (
              <div className="mt-6">
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-900">인재 흐름</p>
                  <p className="text-xs text-gray-500 mt-0.5">최근 12개월 링크드인 기반 인재 이동 현황</p>
                </div>
                <div className="p-4 bg-gray-100 rounded-xl border border-gray-200">
                  <TalentFlowChart
                    talentFlow={(profile as unknown as Record<string, unknown>).talentFlow as TalentFlow}
                    companyName={profile.name}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}
