import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useCompanyComparison } from '../../hooks/useCompanyDna'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { CardSkeleton } from '../common/LoadingSkeleton'
import { EmptyState } from '../common/EmptyState'
import type { CompanyDnaResponse } from '../../types/companyDna'

// 만원 단위 포맷
function fmtWan(val: number | null): string {
  if (val === null) return '데이터 없음'
  return `${Math.round(val / 10000).toLocaleString()}만원`
}

// 퍼센트 포맷
function fmtPct(val: number): string {
  return `${Math.round(val * 100)}%`
}

// 전체 점수에 따른 텍스트 색상
function scoreTextColor(score: number): string {
  if (score >= 70) return 'text-green-600'
  if (score >= 40) return 'text-yellow-600'
  return 'text-red-600'
}

function buildRadarData(dataA: CompanyDnaResponse, dataB: CompanyDnaResponse) {
  return [
    {
      axis: '기술',
      companyA: dataA.tech.diversityScore,
      companyB: dataB.tech.diversityScore,
    },
    {
      axis: '채용',
      companyA: dataA.hiring.intensityScore,
      companyB: dataB.hiring.intensityScore,
    },
    {
      axis: '연봉',
      companyA: dataA.compensation.positionPercentile ?? 50,
      companyB: dataB.compensation.positionPercentile ?? 50,
    },
    {
      axis: '문화',
      companyA: dataA.culture.cultureScore,
      companyB: dataB.culture.cultureScore,
    },
  ]
}

// 점수 비교 테이블 행
function ScoreRow({ label, a, b }: { label: string; a: number; b: number }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
      <span className="w-16 text-xs text-gray-500">{label}</span>
      <div className="flex-1 flex items-center gap-2">
        <span className={`text-sm font-semibold w-10 text-right ${scoreTextColor(a)}`}>{a}</span>
        <div className="flex-1 bg-gray-100 rounded-full h-2 relative">
          <div
            className="absolute left-0 top-0 h-2 rounded-full bg-blue-400 opacity-70"
            style={{ width: `${a}%` }}
          />
          <div
            className="absolute left-0 top-0 h-2 rounded-full bg-orange-400 opacity-70"
            style={{ width: `${b}%` }}
          />
        </div>
        <span className={`text-sm font-semibold w-10 ${scoreTextColor(b)}`}>{b}</span>
      </div>
    </div>
  )
}

// 단일 기업 DNA 카드 (상세 비교용)
function DnaDetailColumn({ dna }: { dna: CompanyDnaResponse }) {
  return (
    <div className="space-y-4">
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
          <div className="flex flex-wrap gap-1">
            {dna.tech.topTechs.slice(0, 6).map((t) => (
              <span key={t.name} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-md">
                {t.name}
                <span className="text-blue-400 ml-1">{t.count}</span>
              </span>
            ))}
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
            <p className="text-xs text-gray-500">성장 단계</p>
            <p className="font-medium text-gray-900">{dna.hiring.growthLabel}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">성장 속도</p>
            {dna.hiring.growthVelocity !== null ? (
              <p className={`font-medium text-xs ${dna.hiring.growthVelocity >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {dna.hiring.growthVelocity >= 0 ? '+' : ''}{dna.hiring.growthVelocity.toFixed(1)}%/주
              </p>
            ) : (
              <p className="text-gray-400 text-xs">데이터 부족</p>
            )}
          </div>
        </div>
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
            <p className="text-xs text-gray-500">시장 포지션</p>
            <p className="font-medium text-gray-900">{dna.compensation.positionLabel}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">스톡옵션</p>
            <p className="font-medium text-gray-900">{fmtPct(dna.compensation.equityRatio)}</p>
          </div>
        </div>
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
            <p className="font-medium text-gray-900">{dna.culture.growthStage ?? '미분류'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">문화 점수</p>
            <p className={`font-medium ${scoreTextColor(dna.culture.cultureScore)}`}>
              {dna.culture.cultureScore}/100
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">신규 포지션</p>
            <p className="font-medium text-gray-900">{fmtPct(dna.culture.newPositionRatio)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export function CompanyCompareView() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [inputA, setInputA] = useState(searchParams.get('a') ?? '')
  const [inputB, setInputB] = useState(searchParams.get('b') ?? '')

  const companyA = searchParams.get('a')
  const companyB = searchParams.get('b')

  const { data: comparison, isLoading, error } = useCompanyComparison(companyA, companyB)

  function handleCompare() {
    const a = inputA.trim()
    const b = inputB.trim()
    if (a && b) {
      setSearchParams({ a, b })
    }
  }

  const radarData =
    comparison ? buildRadarData(comparison.companyA, comparison.companyB) : null

  return (
    <ErrorBoundary>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">기업 비교</h1>
            <p className="mt-1 text-sm text-gray-500">
              두 기업의 DNA를 나란히 비교합니다.
            </p>
          </div>
          <Link
            to="/dashboard/company-dna"
            className="px-3 py-1.5 text-xs border border-gray-200 rounded-md hover:bg-gray-50 transition-colors text-gray-600"
          >
            회사 DNA로 돌아가기
          </Link>
        </div>

        {/* Search inputs */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 w-14">기업 A</span>
            <input
              value={inputA}
              onChange={(e) => setInputA(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleCompare() }}
              placeholder="예: 토스"
              className="w-40 px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-100 text-gray-900 focus:outline-none focus:border-gray-400"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 w-14">기업 B</span>
            <input
              value={inputB}
              onChange={(e) => setInputB(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleCompare() }}
              placeholder="예: 카카오"
              className="w-40 px-3 py-2 text-sm border border-gray-200 rounded-md bg-gray-100 text-gray-900 focus:outline-none focus:border-gray-400"
            />
          </div>
          <button
            onClick={handleCompare}
            disabled={!inputA.trim() || !inputB.trim()}
            className="px-4 py-2 text-xs bg-gray-900 text-white rounded-md hover:bg-gray-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            비교하기
          </button>
        </div>

        {/* Empty state */}
        {!companyA && !companyB && (
          <EmptyState
            title="비교할 기업을 입력하세요"
            description="두 기업명을 입력하고 '비교하기' 버튼을 눌러 DNA를 비교합니다."
          />
        )}

        {/* Loading */}
        {companyA && companyB && isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
        )}

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500">
            비교 데이터를 불러오는 중 오류가 발생했습니다.
          </p>
        )}

        {/* Comparison result */}
        {!isLoading && !error && comparison && radarData && (
          <>
            {/* Company name headers */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded-xl border border-blue-100 text-center">
                <p className="text-sm font-semibold text-blue-700">{comparison.companyA.companyName}</p>
                <p className="text-xs text-blue-400 mt-0.5">{comparison.companyA.week} 기준</p>
                <p className={`text-lg font-bold mt-1 ${scoreTextColor(comparison.companyA.overallScore)}`}>
                  {comparison.companyA.overallScore}
                  <span className="text-xs text-gray-400 font-normal">/100</span>
                </p>
              </div>
              <div className="p-3 bg-orange-50 rounded-xl border border-orange-100 text-center">
                <p className="text-sm font-semibold text-orange-700">{comparison.companyB.companyName}</p>
                <p className="text-xs text-orange-400 mt-0.5">{comparison.companyB.week} 기준</p>
                <p className={`text-lg font-bold mt-1 ${scoreTextColor(comparison.companyB.overallScore)}`}>
                  {comparison.companyB.overallScore}
                  <span className="text-xs text-gray-400 font-normal">/100</span>
                </p>
              </div>
            </div>

            {/* Radar + Score table */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Radar Chart */}
              <div className="p-4 bg-white rounded-xl border border-gray-200">
                <p className="text-sm font-semibold text-gray-900 mb-3">DNA 레이더</p>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12, fill: '#6b7280' }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                      name={comparison.companyA.companyName}
                      dataKey="companyA"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                    <Radar
                      name={comparison.companyB.companyName}
                      dataKey="companyB"
                      stroke="#f97316"
                      fill="#f97316"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Score comparison table */}
              <div className="p-4 bg-white rounded-xl border border-gray-200">
                <p className="text-sm font-semibold text-gray-900 mb-3">점수 비교</p>
                <div className="flex items-center justify-between mb-3 px-1">
                  <span className="text-xs font-medium text-blue-500">{comparison.companyA.companyName}</span>
                  <span className="text-xs font-medium text-orange-500">{comparison.companyB.companyName}</span>
                </div>
                <ScoreRow
                  label="기술"
                  a={comparison.companyA.tech.diversityScore}
                  b={comparison.companyB.tech.diversityScore}
                />
                <ScoreRow
                  label="채용"
                  a={comparison.companyA.hiring.intensityScore}
                  b={comparison.companyB.hiring.intensityScore}
                />
                <ScoreRow
                  label="연봉"
                  a={comparison.companyA.compensation.positionPercentile ?? 50}
                  b={comparison.companyB.compensation.positionPercentile ?? 50}
                />
                <ScoreRow
                  label="문화"
                  a={comparison.companyA.culture.cultureScore}
                  b={comparison.companyB.culture.cultureScore}
                />
                <ScoreRow
                  label="종합"
                  a={comparison.companyA.overallScore}
                  b={comparison.companyB.overallScore}
                />

                {/* Segment benchmark reference */}
                {comparison.segmentBenchmark && (
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      세그먼트 기준 ({comparison.segmentBenchmark.segmentName} · {comparison.segmentBenchmark.companyCount}개사)
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      문화 {comparison.segmentBenchmark.avgCultureScore} · 채용 {comparison.segmentBenchmark.avgHiringScore}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Side-by-side detail cards */}
            <div>
              <p className="text-sm font-semibold text-gray-900 mb-4">상세 비교</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-xs font-semibold text-blue-500 mb-3 px-1">{comparison.companyA.companyName}</p>
                  <DnaDetailColumn dna={comparison.companyA} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-orange-500 mb-3 px-1">{comparison.companyB.companyName}</p>
                  <DnaDetailColumn dna={comparison.companyB} />
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
  )
}
