import { useState } from 'react'
import { apiClient } from '../../services/apiClient'
import { useActionPanel } from '../../hooks/useActionPanel'
import { ActionPanelLayout } from '../common/ActionPanelLayout'
import { ErrorBoundary } from '../common/ErrorBoundary'
import type {
  CandidateProfilerRequest,
  CandidateProfilerResponse,
  CompetingOffer,
} from '../../types/candidateProfiler'

// ---------------------------------------------------------------------------
// TDS 등급 색상
// ---------------------------------------------------------------------------

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

const DIRECTION_LABELS: Record<string, { label: string; desc: string }> = {
  UPWARD:   { label: '상향 지원', desc: '목표 기업이 현재보다 높은 인재 밀도를 요구합니다.' },
  LATERAL:  { label: '수평 지원', desc: '현재 역량과 유사한 수준의 포지션입니다.' },
  DOWNWARD: { label: '하향 지원', desc: '현재 역량이 목표 기업 기준을 상회합니다.' },
}

const LEVERAGE_LABELS: Record<string, { label: string; color: string }> = {
  HIGH:   { label: '높음', color: 'text-green-600' },
  MEDIUM: { label: '보통', color: 'text-yellow-600' },
  LOW:    { label: '낮음', color: 'text-red-600' },
}

const LIKELIHOOD_LABELS: Record<string, string> = {
  HIGH:   '높음',
  MEDIUM: '보통',
  LOW:    '낮음',
}

// ---------------------------------------------------------------------------
// 세그먼트 목록
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
  { value: 'blockchain', label: '블록체인' },
  { value: 'embedded', label: '임베디드/펌웨어' },
  { value: 'game',     label: '게임' },
  { value: 'bi',       label: 'BI/분석' },
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

// ---------------------------------------------------------------------------
// 결과 카드 컴포넌트
// ---------------------------------------------------------------------------

function TdsScoreCard({ result }: { result: CandidateProfilerResponse }) {
  const gradeColor = GRADE_COLORS[result.tdsGrade] ?? 'text-gray-600'
  const gradeBg = GRADE_BG[result.tdsGrade] ?? 'bg-gray-100 border-gray-300'
  return (
    <div className="flex items-center gap-6 p-5 bg-gray-50 rounded-xl border border-gray-200 mb-4">
      <div className="text-center">
        <div className="text-5xl font-bold text-gray-900">{result.tdsScore}</div>
        <div className="text-xs text-gray-500 mt-1">TDS 점수</div>
      </div>
      <div className="flex flex-col gap-2">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${gradeBg} ${gradeColor}`}>
          {result.tdsGrade}등급
        </span>
        <span className="text-sm text-gray-600">상위 {result.tdsPercentile}%</span>
      </div>
    </div>
  )
}

function DirectionCard({ result }: { result: CandidateProfilerResponse }) {
  const dir = DIRECTION_LABELS[result.applicationDirection.type] ?? DIRECTION_LABELS['LATERAL']
  return (
    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
      <div className="text-xs text-gray-500 mb-1">지원 방향성</div>
      <div className="text-sm font-semibold text-gray-900 mb-1">{dir.label}</div>
      <p className="text-xs text-gray-500 leading-relaxed">{dir.desc}</p>
    </div>
  )
}

function SalaryCard({ result }: { result: CandidateProfilerResponse }) {
  const { marketP25, marketP50, marketP75, recommendedLeverage } = result.salaryNegotiation
  const lev = LEVERAGE_LABELS[recommendedLeverage] ?? LEVERAGE_LABELS['MEDIUM']
  return (
    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
      <div className="text-xs text-gray-500 mb-2">연봉 협상력</div>
      <div className="flex justify-between text-xs text-gray-600 mb-2">
        <span>P25: {marketP25.toLocaleString()}만</span>
        <span>P50: {marketP50.toLocaleString()}만</span>
        <span>P75: {marketP75.toLocaleString()}만</span>
      </div>
      <div className="text-xs text-gray-500">
        레버리지:{' '}
        <span className={`font-semibold ${lev.color}`}>{lev.label}</span>
      </div>
    </div>
  )
}

function OffersCard({ offers }: { offers: CompetingOffer[] }) {
  return (
    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
      <div className="text-xs text-gray-500 mb-2">경쟁 오퍼 Top3</div>
      <div className="flex flex-col gap-1.5">
        {offers.map((o, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span className="text-gray-900 font-medium">{o.companyName}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">TDS {o.tdsScore}</span>
              <span className="text-xs text-gray-400">{LIKELIHOOD_LABELS[o.likelihood]}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 메인 뷰
// ---------------------------------------------------------------------------

type TabType = 'resume' | 'structured'

export function CandidateProfilerView() {
  const [activeTab, setActiveTab] = useState<TabType>('resume')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<CandidateProfilerResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 레쥬메 탭 상태
  const [resumeText, setResumeText] = useState('')

  // 직접 입력 탭 상태
  const [currentCompany, setCurrentCompany] = useState('')
  const [yearsOfExperience, setYearsOfExperience] = useState<number | ''>('')
  const [education, setEducation] = useState('')
  const [skillInput, setSkillInput] = useState('')
  const [skills, setSkills] = useState<string[]>([])
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

  const handleAnalyze = async () => {
    setError(null)
    setResult(null)

    const req: CandidateProfilerRequest = {}
    if (activeTab === 'resume') {
      if (!resumeText.trim()) return
      req.resumeText = resumeText.slice(0, 3000)
    } else {
      if (!currentCompany && skills.length === 0) return
      if (currentCompany) req.currentCompany = currentCompany
      if (yearsOfExperience !== '') req.yearsOfExperience = Number(yearsOfExperience)
      if (education) req.education = education
      if (skills.length > 0) req.skills = skills
      if (targetSegment) req.targetSegment = targetSegment
    }

    setIsLoading(true)
    try {
      const { data } = await apiClient.post<{ status: string; data: CandidateProfilerResponse }>(
        '/api/v1/candidate-profiler',
        req,
      )
      setResult(data.data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        ?? (err instanceof Error ? err.message : '분석 중 오류가 발생했습니다.')
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
  }

  const panelProps = useActionPanel('candidate-profiler')

  return (
    <ActionPanelLayout panel={panelProps}>
      <ErrorBoundary>
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-lg font-semibold text-gray-900">후보자 프로파일러</h1>
            <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full font-medium">
              HR 인하우스 전용
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            후보자 정보를 입력하면 TDS 기반 채용 판단 정보를 제공합니다.
          </p>

          {/* 결과가 없을 때만 입력 섹션 표시 */}
          {!result && (
            <>
              {/* 탭 */}
              <div className="flex gap-1 mb-4 border-b border-gray-200">
                <button
                  onClick={() => setActiveTab('resume')}
                  className={`px-4 py-2 text-sm transition-colors ${
                    activeTab === 'resume'
                      ? 'text-gray-900 font-medium border-b-2 border-gray-900 -mb-px'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  레쥬메 붙여넣기
                </button>
                <button
                  onClick={() => setActiveTab('structured')}
                  className={`px-4 py-2 text-sm transition-colors ${
                    activeTab === 'structured'
                      ? 'text-gray-900 font-medium border-b-2 border-gray-900 -mb-px'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  직접 입력
                </button>
              </div>

              {/* 레쥬메 탭 */}
              {activeTab === 'resume' && (
                <div>
                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value.slice(0, 3000))}
                    placeholder="이력서 내용을 붙여넣으세요 (최대 3,000자)..."
                    className="w-full min-h-[160px] text-sm p-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-900 resize-y font-sans focus:outline-none focus:border-gray-400"
                    rows={7}
                  />
                  <div className="text-xs text-gray-400 text-right mt-1">
                    {resumeText.length} / 3,000
                  </div>
                </div>
              )}

              {/* 직접 입력 탭 */}
              {activeTab === 'structured' && (
                <div className="flex flex-col gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">현재 재직사</label>
                    <input
                      type="text"
                      value={currentCompany}
                      onChange={(e) => setCurrentCompany(e.target.value)}
                      placeholder="예: 카카오"
                      className="w-full text-sm p-2.5 border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:border-gray-400"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">경력</label>
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
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">타겟 세그먼트</label>
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
              )}

              {/* 분석 버튼 */}
              <button
                onClick={handleAnalyze}
                disabled={isLoading}
                className="mt-4 px-5 py-2 text-sm bg-gray-900 text-white rounded-lg hover:opacity-85 transition-opacity disabled:opacity-40 flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    분석 중...
                  </>
                ) : (
                  '후보자 분석 →'
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
              <TdsScoreCard result={result} />

              <div className="grid grid-cols-1 gap-3 mb-4">
                <DirectionCard result={result} />
                <SalaryCard result={result} />
                <OffersCard offers={result.competingOffers} />
              </div>

              {result.summary && (
                <p className="text-sm text-gray-600 leading-relaxed mb-4 px-1">
                  {result.summary}
                </p>
              )}

              <button
                onClick={handleReset}
                className="px-4 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
              >
                다시 분석
              </button>
            </div>
          )}
        </div>
      </ErrorBoundary>
    </ActionPanelLayout>
  )
}
