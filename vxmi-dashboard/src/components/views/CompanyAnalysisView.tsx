import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  LineChart,
  Line,
  Tooltip,
} from 'recharts'
import { useCompanyAnalysis } from '../../hooks/useDashboard'
import { SparkBars } from '../common/SparkBars'

const DEFAULT_COMPANY_BTNS = ['토스', '카카오', '네이버', '삼성전자', '쿠팡']
import { TalentFlowChart } from '../common/TalentFlowChart'
import type { TalentFlow, CompanyProfile } from '../../types/dashboard'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'

// 5축 레이더 데이터 빌드 (0~100 스케일로 변환)
function buildRadarData(profile: CompanyProfile) {
  return [
    {
      axis: '인재밀도',
      value: Math.round(profile.talentDensity.overall),
    },
    {
      axis: '채용파워',
      value: Math.round(profile.hiringPower.overall),
    },
    {
      axis: '성장성',
      value: Math.round(profile.growthScore * 100),
    },
    {
      axis: '기술다양성',
      value: Math.round(profile.techDiversity * 100),
    },
    {
      axis: '연봉경쟁력',
      value: Math.round(profile.salaryCompetitiveness * 100),
    },
  ]
}

// HiringVelocity SparkLine — weeklyTrend 기반 compact 라인 차트
function HiringVelocitySparkLine({ trend, velocity }: { trend: number[]; velocity: number }) {
  const data = trend.map((v, i) => ({ i, v }))
  const pct = Math.round(velocity * 100)
  return (
    <div>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl font-medium text-gray-900">{pct}</span>
        <span className="text-xs text-gray-500">/100 · 채용속도 지수</span>
      </div>
      {data.length >= 2 ? (
        <ResponsiveContainer width="100%" height={40}>
          <LineChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
            <Line
              type="monotone"
              dataKey="v"
              stroke="#6366f1"
              strokeWidth={1.5}
              dot={false}
            />
            <Tooltip
              contentStyle={{ fontSize: 11, padding: '2px 6px' }}
              formatter={(v: unknown) => [Number(v), '공고수']}
              labelFormatter={() => ''}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-xs text-gray-400">추이 데이터 없음</p>
      )}
    </div>
  )
}

export function CompanyAnalysisView() {
  const [selectedCompany, setSelectedCompany] = useState('토스')
  const [inputVal, setInputVal] = useState('')
  const navigate = useNavigate()

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
            <div className="flex items-center justify-end mb-3">
              <button
                onClick={() => navigate(`/dashboard/company-dna?company=${encodeURIComponent(profile.companyId)}`)}
                className="px-3 py-1.5 text-xs border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-gray-700"
              >
                DNA 프로필 보기 →
              </button>
            </div>

            {/* Radar Chart — 5축 */}
            <div className="mb-4 p-4 bg-white rounded-xl border border-gray-200">
              <p className="text-sm font-medium text-gray-900 mb-1">종합 역량 레이더</p>
              <p className="text-xs text-gray-400 mb-2">인재밀도 · 채용파워 · 성장성 · 기술다양성 · 연봉경쟁력</p>
              <ResponsiveContainer width="100%" height={240}>
                <RadarChart data={buildRadarData(profile)} margin={{ top: 8, right: 20, bottom: 8, left: 20 }}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11, fill: '#6b7280' }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    name={profile.name}
                    dataKey="value"
                    stroke="#6366f1"
                    fill="#6366f1"
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

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

              {/* Panel C: Hiring Velocity SparkLine */}
              <div className="p-4 bg-gray-100 rounded-xl border border-gray-200">
                <p className="text-xs text-gray-500 mb-2">채용 속도 트렌드</p>
                <HiringVelocitySparkLine
                  trend={profile.hiringPower.weeklyTrend}
                  velocity={profile.hiringVelocity}
                />
              </div>

              {/* Panel D: Growth + Salary */}
              <div className="p-4 bg-gray-100 rounded-xl border border-gray-200 space-y-3">
                <div>
                  <p className="text-xs text-gray-500 mb-1">성장성 점수</p>
                  <p className="text-2xl font-medium text-gray-900">
                    {Math.round(profile.growthScore * 100)}
                    <span className="text-sm text-gray-500 font-normal">/100</span>
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">연봉 경쟁력</p>
                  <p className="text-2xl font-medium text-gray-900">
                    {Math.round(profile.salaryCompetitiveness * 100)}
                    <span className="text-sm text-gray-500 font-normal">/100</span>
                  </p>
                </div>
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
