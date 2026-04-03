import { useState } from 'react'
import { apiClient } from '../../services/apiClient'
import { useAuthStore } from '../../stores/authStore'
import { useActionPanel } from '../../hooks/useActionPanel'
import { ActionPanelLayout } from '../common/ActionPanelLayout'
import { ErrorBoundary } from '../common/ErrorBoundary'

// ---------------------------------------------------------------------------
// 타입 정의
// ---------------------------------------------------------------------------

interface MarketValueRequest {
  skills?: string[]
  education?: string
  yearsOfExperience?: number
  currentCompany?: string
  targetSegment?: string
}

interface MarketValueResponse {
  estimatedValueP25: number
  estimatedValueP50: number
  estimatedValueP75: number
  tdsScore: number
  tdsGrade: string
  tdsPercentile: number
  segmentRank: string
  valueDrivers: string[]
  improvementTips: string[]
}

// ---------------------------------------------------------------------------
// 상수
// ---------------------------------------------------------------------------

const SEGMENTS = [
  { value: 'backend',  label: '백엔드' },
  { value: 'frontend', label: '프론트엔드' },
  { value: 'mobile',   label: '모바일' },
  { value: 'ai-ml',    label: 'AI/ML' },
  { value: 'data',     label: '데이터' },
  { value: 'devops',   label: 'DevOps/인프라' },
  { value: 'security', label: '보안' },
  { value: 'pm',       label: 'PM/기획' },
  { value: 'design',   label: '디자인' },
  { value: 'qa',       label: 'QA' },
]

const YEAR_OPTIONS = [
  { value: 1,  label: '1년' },
  { value: 2,  label: '2년' },
  { value: 3,  label: '3년' },
  { value: 4,  label: '4년' },
  { value: 5,  label: '5년' },
  { value: 7,  label: '7년' },
  { value: 10, label: '10년' },
  { value: 15, label: '15년' },
  { value: 20, label: '20년 이상' },
]

const GRADE_COLORS: Record<string, string> = {
  S: 'text-purple-600',
  A: 'text-blue-600',
  B: 'text-green-600',
  C: 'text-yellow-600',
  D: 'text-red-600',
}

const GRADE_BG: Record<string, string> = {
  S: 'bg-purple-100 border-purple-300',
  A: 'bg-blue-100 border-blue-300',
  B: 'bg-green-100 border-green-300',
  C: 'bg-yellow-100 border-yellow-300',
  D: 'bg-red-100 border-red-300',
}

// ---------------------------------------------------------------------------
// 메인 뷰
// ---------------------------------------------------------------------------

export function MarketValueView() {
  const { user } = useAuthStore()
  const isJobSeeker = user?.category === 'JOB_SEEKER'

  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<MarketValueResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [skillInput, setSkillInput] = useState('')
  const [skills, setSkills] = useState<string[]>([])
  const [education, setEducation] = useState('')
  const [yearsOfExperience, setYearsOfExperience] = useState<number | ''>('')
  const [currentCompany, setCurrentCompany] = useState('')
  const [targetSegment, setTargetSegment] = useState('')

  const handleAddSkill = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault()
      const trimmed = skillInput.trim()
      if (!skills.includes(trimmed)) {
        setSkills((prev) => [...prev, trimmed])
      }
      setSkillInput('')
    }
  }

  const handleRemoveSkill = (skill: string) => {
    setSkills((prev) => prev.filter((s) => s !== skill))
  }

  const handleCalculate = async () => {
    setError(null)
    setResult(null)

    const req: MarketValueRequest = {}
    if (skills.length > 0) req.skills = skills
    if (education) req.education = education
    if (yearsOfExperience !== '') req.yearsOfExperience = Number(yearsOfExperience)
    if (currentCompany) req.currentCompany = currentCompany
    if (targetSegment) req.targetSegment = targetSegment

    setIsLoading(true)
    try {
      const { data } = await apiClient.post<{ status: string; data: MarketValueResponse }>(
        '/api/v1/market-value',
        req,
      )
      setResult(data.data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? (err instanceof Error ? err.message : '계산 중 오류가 발생했습니다.')
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
  }

  const panelProps = useActionPanel('market-value')

  const mainContent = (
    <ActionPanelLayout panel={panelProps}>
      <ErrorBoundary>
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-lg font-semibold text-gray-900">내 시장가치</h1>
            <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full font-medium">
              구직자 전용
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            스킬과 경력을 입력하면 현재 시장 기준 예상 연봉 범위를 알려드립니다.
          </p>

          {/* 입력 폼 */}
          {!result && (
            <>
              <div className="flex flex-col gap-3">
                {/* 스킬 */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">스킬 (Enter로 추가)</label>
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={handleAddSkill}
                    placeholder="예: Python, React, AWS..."
                    className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                  />
                  {skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {skills.map((s) => (
                        <span
                          key={s}
                          className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-gray-100 border border-gray-200 rounded-md text-gray-700"
                        >
                          {s}
                          <button
                            onClick={() => handleRemoveSkill(s)}
                            className="text-gray-400 hover:text-gray-700 leading-none"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* 학력 */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">학력</label>
                  <input
                    type="text"
                    value={education}
                    onChange={(e) => setEducation(e.target.value)}
                    placeholder="예: 서울대 컴퓨터공학 학사"
                    className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                  />
                </div>

                {/* 경력 연수 */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">경력 연수</label>
                  <select
                    value={yearsOfExperience}
                    onChange={(e) => setYearsOfExperience(e.target.value === '' ? '' : Number(e.target.value))}
                    className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                  >
                    <option value="">선택</option>
                    {YEAR_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>

                {/* 현재 재직사 */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">현재 재직사 (선택사항)</label>
                  <input
                    type="text"
                    value={currentCompany}
                    onChange={(e) => setCurrentCompany(e.target.value)}
                    placeholder="예: 카카오"
                    className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                  />
                </div>

                {/* 목표 세그먼트 */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">목표 세그먼트</label>
                  <select
                    value={targetSegment}
                    onChange={(e) => setTargetSegment(e.target.value)}
                    className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                  >
                    <option value="">선택 (선택사항)</option>
                    {SEGMENTS.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={handleCalculate}
                disabled={isLoading}
                className="mt-4 px-5 py-2 text-sm bg-gray-900 text-white rounded-lg hover:opacity-85 transition-opacity disabled:opacity-40 flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    계산 중...
                  </>
                ) : (
                  '시장가치 계산 →'
                )}
              </button>

              {error && (
                <p className="mt-2 text-xs text-red-500">{error}</p>
              )}
            </>
          )}

          {/* 결과 섹션 */}
          {result && (
            <div>
              {/* TDS 점수 카드 */}
              <div className="flex items-center gap-6 p-5 bg-gray-50 rounded-xl border border-gray-200 mb-4">
                <div className="text-center">
                  <div className="text-5xl font-bold text-gray-900">{result.tdsScore}</div>
                  <div className="text-xs text-gray-500 mt-1">TDS 점수</div>
                </div>
                <div className="flex flex-col gap-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${GRADE_BG[result.tdsGrade] ?? 'bg-gray-100 border-gray-300'} ${GRADE_COLORS[result.tdsGrade] ?? 'text-gray-600'}`}>
                    {result.tdsGrade}등급
                  </span>
                  <span className="text-sm text-gray-600">상위 {result.tdsPercentile}%</span>
                  <span className="text-xs text-gray-500">{result.segmentRank}</span>
                </div>
              </div>

              {/* 연봉 범위 바 */}
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 mb-3">
                <div className="text-xs text-gray-500 mb-3">예상 연봉 범위</div>
                <div className="space-y-2">
                  {[
                    { label: 'P25 (하위 기준)', value: result.estimatedValueP25, color: 'bg-gray-300' },
                    { label: 'P50 (중간)', value: result.estimatedValueP50, color: 'bg-blue-500' },
                    { label: 'P75 (상위 기준)', value: result.estimatedValueP75, color: 'bg-indigo-600' },
                  ].map(({ label, value, color }) => (
                    <div key={label}>
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>{label}</span>
                        <span className="font-semibold text-gray-900">{value.toLocaleString()}만원</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className={`${color} h-2 rounded-full transition-all`}
                          style={{ width: `${Math.min((value / result.estimatedValueP75) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 강점 요소 */}
              {result.valueDrivers.length > 0 && (
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200 mb-3">
                  <div className="text-xs font-medium text-emerald-700 mb-2">강점 요소</div>
                  <ul className="space-y-1">
                    {result.valueDrivers.map((d, i) => (
                      <li key={i} className="text-xs text-emerald-800 flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0">•</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 개선 팁 */}
              {result.improvementTips.length > 0 && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 mb-4">
                  <div className="text-xs font-medium text-amber-700 mb-2">개선 팁</div>
                  <ul className="space-y-1">
                    {result.improvementTips.map((t, i) => (
                      <li key={i} className="text-xs text-amber-800 flex items-start gap-1.5">
                        <span className="mt-0.5 shrink-0">→</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={handleReset}
                className="px-4 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
              >
                다시 계산
              </button>
            </div>
          )}
        </div>
      </ErrorBoundary>
    </ActionPanelLayout>
  )

  // JOB_SEEKER가 아닌 경우 blur 오버레이 표시
  if (!isJobSeeker) {
    return (
      <div className="relative">
        <div className="blur-sm pointer-events-none select-none">
          {mainContent}
        </div>
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 px-8 py-6 text-center max-w-sm">
            <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-emerald-500" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-gray-900 mb-1">구직자 전용 뷰</h2>
            <p className="text-sm text-gray-500">
              시장가치 뷰는 구직자(JOB_SEEKER) 전용 기능입니다.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return mainContent
}
