import { useState } from 'react'
import { PLACEHOLDER_COMPANIES } from '../../data/companies'
import { SEGMENTS } from '../../data/segments'
import { searchByKeyword } from '../../data/keywordMap'
import { MetricCard } from '../common/MetricCard'
import { TreeMapChart } from '../charts/TreeMapChart'

export function TopCompaniesView() {
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState(() => new Date().toISOString().split('T')[0])
  const [keyword, setKeyword] = useState('')
  const [activeKeyword, setActiveKeyword] = useState('')
  const [matchedSegmentIds, setMatchedSegmentIds] = useState<string[]>([])

  const handleSearch = () => {
    const trimmed = keyword.trim()
    setActiveKeyword(trimmed)
    if (trimmed) {
      setMatchedSegmentIds(searchByKeyword(trimmed))
    } else {
      setMatchedSegmentIds([])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSearch()
  }

  // Map segment IDs to segment names for filtering
  const matchedSegmentNames = matchedSegmentIds.map(id => {
    const seg = SEGMENTS.find(s => s.id === id)
    return seg ? seg.name : null
  }).filter(Boolean) as string[]

  const filteredCompanies = activeKeyword && matchedSegmentNames.length > 0
    ? PLACEHOLDER_COMPANIES.filter(c => matchedSegmentNames.includes(c.segment))
    : PLACEHOLDER_COMPANIES

  const dateFilterActive = fromDate || toDate

  return (
    <div>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <MetricCard label="총 채용 기업" value="2,847" sub="이번 주 집계" />
        <MetricCard label="Top 20 점유율" value="23%" sub="전체 공고 기준" />
        <MetricCard label="최다 채용" value="삼성전자" sub="248 포지션" />
        <MetricCard label="신흥 기업" value="토스" sub="전주比 +18%" />
      </div>

      {/* Filter Bar */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-3 mb-4">
        <div className="flex flex-wrap items-end gap-4">
          {/* Date Range */}
          <div className="flex items-center gap-2">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-gray-500">From</span>
              <input
                type="date"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
              />
            </div>
            <span className="text-xs text-gray-400 mt-4">~</span>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-gray-500">To</span>
              <input
                type="date"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
              />
            </div>
          </div>

          {/* Divider */}
          <div className="w-px h-8 bg-gray-200 self-end mb-0.5" />

          {/* Keyword Search */}
          <div className="flex flex-col gap-0.5">
            <span className="text-xs text-gray-500">키워드 검색</span>
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="예: 백엔드, AI, 마케팅..."
                className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 w-48 focus:outline-none focus:ring-1 focus:ring-gray-300 placeholder:text-gray-300"
              />
              <button
                onClick={handleSearch}
                className="text-xs px-3 py-1.5 bg-gray-800 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                검색
              </button>
              {(activeKeyword || dateFilterActive) && (
                <button
                  onClick={() => {
                    setFromDate('')
                    setToDate('')
                    setKeyword('')
                    setActiveKeyword('')
                    setMatchedSegmentIds([])
                  }}
                  className="text-xs px-2 py-1.5 bg-white border border-gray-200 text-gray-500 rounded-md hover:bg-gray-100 transition-colors"
                >
                  초기화
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Matched Segment Badges */}
        {activeKeyword && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            {matchedSegmentIds.length > 0 ? (
              <>
                <span className="text-xs text-gray-400">매칭된 직군:</span>
                {matchedSegmentIds.map(id => {
                  const seg = SEGMENTS.find(s => s.id === id)
                  if (!seg) return null
                  return (
                    <span
                      key={id}
                      className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{ backgroundColor: seg.color + '22', color: seg.color }}
                    >
                      {seg.name}
                    </span>
                  )
                })}
              </>
            ) : (
              <span className="text-xs text-gray-400">"{activeKeyword}"에 매칭된 직군이 없습니다.</span>
            )}
          </div>
        )}

        {/* Date filter info */}
        {dateFilterActive && (
          <p className="mt-2 text-xs text-gray-400">* 기간 필터는 백엔드 연동 후 활성화됩니다</p>
        )}
      </div>

      <TreeMapChart data={filteredCompanies} />
    </div>
  )
}
