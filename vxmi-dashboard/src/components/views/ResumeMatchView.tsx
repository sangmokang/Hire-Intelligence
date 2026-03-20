import { useState } from 'react'
import { SAMPLE_RESUME, MATCH_DB, SCORE_COLORS } from '../../data/resume'
import type { MatchResult } from '../../types'

export function ResumeMatchView() {
  const [resumeText, setResumeText] = useState('')
  const [results, setResults] = useState<MatchResult[]>([])
  const [isMatching, setIsMatching] = useState(false)

  const handleMatch = async () => {
    if (!resumeText.trim()) return
    setIsMatching(true)

    // 하드코딩 데이터 기반 매칭 (백엔드 연동 예정)
    await new Promise((r) => setTimeout(r, 600))
    setResults(MATCH_DB)
    setIsMatching(false)
  }

  return (
    <div>
      <p className="text-sm text-gray-500 mb-3">
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
          disabled={isMatching || !resumeText.trim()}
          className="px-4 py-1.5 text-xs bg-gray-900 text-white rounded-md hover:opacity-85 transition-opacity disabled:opacity-40"
        >
          {isMatching ? '분석 중...' : '관련 기업 매칭 →'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="grid grid-cols-2 gap-3 mt-4">
          {results.map((r, i) => {
            const color = SCORE_COLORS[r.company] ?? '#888780'
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
      )}
    </div>
  )
}
