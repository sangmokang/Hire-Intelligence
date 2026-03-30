import { useState } from 'react'
import { useCompanyDna, useSegmentBenchmark } from '../../hooks/useCompanyDna'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'

const DEFAULT_COMPANY_BTNS = ['토스', '카카오', '네이버', '삼성전자', '쿠팡']

// 전체 점수에 따른 색상 클래스
function scoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500'
  if (score >= 40) return 'bg-yellow-500'
  return 'bg-red-500'
}

// 전체 점수에 따른 텍스트 색상
function scoreTextColor(score: number): string {
  if (score >= 70) return 'text-green-600'
  if (score >= 40) return 'text-yellow-600'
  return 'text-red-600'
}

// 만원 단위 포맷
function fmtWan(val: number | null): string {
  if (val === null) return '데이터 없음'
  return `${Math.round(val / 10000).toLocaleString()}만원`
}

// 퍼센트 포맷
function fmtPct(val: number): string {
  return `${Math.round(val * 100)}%`
}

export function CompanyDnaView() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [inputVal, setInputVal] = useState('')

  const { data: dna, isLoading, error } = useCompanyDna(selectedCompany)
  const { data: benchmark } = useSegmentBenchmark(dna?.segmentId ?? null)

  function handleSearch(name: string) {
    const trimmed = name.trim()
    if (trimmed) setSelectedCompany(trimmed)
  }

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-xl font-semibold text-gray-900">회사 DNA</h1>
          <p className="mt-1 text-sm text-gray-500">
            기업의 기술 스택, 채용 패턴, 보상 구조, 문화 신호를 종합 분석합니다.
          </p>
        </div>

        {/* Quick-select buttons */}
        <div className="flex flex-wrap gap-2">
          {DEFAULT_COMPANY_BTNS.map((c) => (
            <button
              key={c}
              onClick={() => handleSearch(c)}
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
        <div className="flex gap-2">
          <input
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(inputVal) }}
            placeholder="기업명 입력..."
            className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-100 text-gray-900 focus:outline-none focus:border-gray-400"
          />
          <button
            onClick={() => handleSearch(inputVal)}
            className="px-4 py-2 text-xs border border-gray-200 rounded-md hover:bg-gray-100 transition-colors"
          >
            분석
          </button>
        </div>

        {/* No company selected */}
        {!selectedCompany && (
          <EmptyState
            title="기업을 선택하세요"
            description="위에서 기업을 선택하거나 이름을 입력하여 DNA 분석을 시작합니다."
          />
        )}

        {/* Loading */}
        {selectedCompany && isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        )}

        {/* Error */}
        {selectedCompany && error && (
          <p className="text-sm text-red-500">
            "{selectedCompany}" 데이터를 불러오는 중 오류가 발생했습니다.
          </p>
        )}

        {/* No DNA data */}
        {selectedCompany && !isLoading && !error && !dna && (
          <EmptyState
            title={`"${selectedCompany}" DNA 데이터 없음`}
            description="DNA 분석 데이터가 아직 없습니다. 데이터 수집 후 자동으로 생성됩니다."
          />
        )}

        {/* DNA data loaded */}
        {!isLoading && !error && dna && (
          <>
            {/* Company header bar */}
            <div className="p-4 bg-gray-100 rounded-xl border border-gray-200">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-lg font-semibold text-gray-900 truncate">{dna.companyName}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{dna.week} 기준</p>
                </div>

                {/* Overall score */}
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <div className="flex items-baseline gap-1">
                    <span className={`text-2xl font-bold ${scoreTextColor(dna.overallScore)}`}>
                      {dna.overallScore}
                    </span>
                    <span className="text-sm text-gray-400">/100</span>
                  </div>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${scoreColor(dna.overallScore)}`}
                      style={{ width: `${dna.overallScore}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">종합 DNA 점수</p>
                </div>

                {/* Segment benchmark */}
                {benchmark && (
                  <div className="flex flex-col items-end gap-0.5 shrink-0 border-l border-gray-200 pl-4">
                    <p className="text-xs text-gray-500">{benchmark.segmentName} 세그먼트 평균</p>
                    <p className="text-sm font-medium text-gray-700">
                      문화 {benchmark.avgCultureScore} · 채용 {benchmark.avgHiringScore}
                    </p>
                    <p className="text-xs text-gray-400">{benchmark.companyCount}개사 기준</p>
                  </div>
                )}
              </div>
            </div>

            {/* 2x2 card grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* Tech DNA */}
              <div className="p-4 bg-white rounded-xl border border-gray-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">🔧</span>
                  <p className="text-sm font-semibold text-gray-900">Tech DNA</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">기술 스택 수</p>
                    <p className="font-medium text-gray-900">{dna.tech.stackCount}종</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">다양성 지수</p>
                    <p className="font-medium text-gray-900">{dna.tech.diversityIndex.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">다양성 점수</p>
                    <p className={`font-medium ${scoreTextColor(dna.tech.diversityScore)}`}>
                      {dna.tech.diversityScore}/100
                    </p>
                  </div>
                </div>
                {dna.tech.topTechs.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1.5">Top 기술</p>
                    <div className="flex flex-wrap gap-1">
                      {dna.tech.topTechs.slice(0, 8).map((t) => (
                        <span
                          key={t.name}
                          className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-md"
                        >
                          {t.name}
                          <span className="text-blue-400 ml-1">{t.count}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Hiring DNA */}
              <div className="p-4 bg-white rounded-xl border border-gray-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">📊</span>
                  <p className="text-sm font-semibold text-gray-900">Hiring DNA</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">총 공고</p>
                    <p className="font-medium text-gray-900">{dna.hiring.totalPostings}건</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">성장 속도</p>
                    {dna.hiring.growthVelocity !== null ? (
                      <p className={`font-medium ${dna.hiring.growthVelocity >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {dna.hiring.growthVelocity >= 0 ? '+' : ''}{dna.hiring.growthVelocity.toFixed(1)}%/주
                      </p>
                    ) : (
                      <p className="text-gray-400 text-xs">데이터 부족</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">성장 단계</p>
                    <p className="font-medium text-gray-900">{dna.hiring.growthLabel}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">세그먼트 폭</p>
                    <p className="font-medium text-gray-900">{dna.hiring.segmentBreadth}개</p>
                  </div>
                </div>
                {Object.keys(dna.hiring.roleDistribution).length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1.5">직급 분포</p>
                    <div className="space-y-1">
                      {Object.entries(dna.hiring.roleDistribution)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 4)
                        .map(([role, count]) => (
                          <div key={role} className="flex items-center gap-2">
                            <span className="text-xs text-gray-600 w-20 truncate">{role}</span>
                            <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                              <div
                                className="bg-blue-400 h-1.5 rounded-full"
                                style={{
                                  width: `${Math.min(
                                    100,
                                    (count / dna.hiring.totalPostings) * 100
                                  )}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Compensation DNA */}
              <div className="p-4 bg-white rounded-xl border border-gray-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">💰</span>
                  <p className="text-sm font-semibold text-gray-900">Compensation DNA</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">평균 연봉</p>
                    <p className="font-medium text-gray-900">{fmtWan(dna.compensation.salaryAvg)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">연봉 범위</p>
                    <p className="font-medium text-gray-900 text-xs">
                      {fmtWan(dna.compensation.salaryMin)} ~ {fmtWan(dna.compensation.salaryMax)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">시장 포지션</p>
                    <p className="font-medium text-gray-900">{dna.compensation.positionLabel}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">스톡옵션</p>
                    <p className="font-medium text-gray-900">{fmtPct(dna.compensation.equityRatio)}</p>
                  </div>
                </div>
                {dna.compensation.topBenefits.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1.5">주요 복리후생</p>
                    <div className="flex flex-wrap gap-1">
                      {dna.compensation.topBenefits.slice(0, 6).map((b) => (
                        <span
                          key={b}
                          className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-md"
                        >
                          {b}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Culture Signals */}
              <div className="p-4 bg-white rounded-xl border border-gray-200 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-base">🏢</span>
                  <p className="text-sm font-semibold text-gray-900">Culture Signals</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-xs text-gray-500">성장 단계</p>
                    <p className="font-medium text-gray-900">
                      {dna.culture.growthStage ?? '미분류'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">신규 포지션</p>
                    <p className="font-medium text-gray-900">{fmtPct(dna.culture.newPositionRatio)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">문화 점수</p>
                    <p className={`font-medium ${scoreTextColor(dna.culture.cultureScore)}`}>
                      {dna.culture.cultureScore}/100
                    </p>
                  </div>
                </div>
                {dna.culture.teamSizePatterns.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1.5">팀 구성 패턴</p>
                    <div className="flex flex-wrap gap-1">
                      {dna.culture.teamSizePatterns.map((p) => (
                        <span
                          key={p}
                          className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-md"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}
