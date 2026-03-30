import type { SDMatrixDrilldown } from '../../types/dashboard'

interface DrilldownPanelProps {
  segmentId: string | null
  segmentName: string | null
  drilldown: SDMatrixDrilldown | undefined
  isLoading: boolean
  onClose: () => void
}

export function DrilldownPanel({
  segmentId,
  segmentName,
  drilldown,
  isLoading,
  onClose,
}: DrilldownPanelProps) {
  if (!segmentId && !segmentName) return null

  const displayName = drilldown?.segmentName ?? segmentName ?? ''

  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-xl border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">{displayName} — 상세 분석</h3>
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-900">
          닫기
        </button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-6">
          <span className="text-xs text-gray-400">불러오는 중...</span>
        </div>
      )}

      {!isLoading && drilldown && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="p-2 bg-white rounded-md border border-gray-200 text-center">
              <p className="text-xs text-gray-500 mb-0.5">채용 수요</p>
              <p className="text-sm font-medium text-gray-900">{drilldown.demand.toLocaleString()}</p>
            </div>
            <div className="p-2 bg-white rounded-md border border-gray-200 text-center">
              <p className="text-xs text-gray-500 mb-0.5">인재 공급</p>
              <p className="text-sm font-medium text-gray-900">{drilldown.supply.toLocaleString()}</p>
            </div>
            <div className="p-2 bg-white rounded-md border border-gray-200 text-center">
              <p className="text-xs text-gray-500 mb-0.5">S/D 비율</p>
              <p className="text-sm font-medium text-gray-900">{drilldown.sdRatio.toFixed(2)}</p>
            </div>
          </div>

          {/* Extra stats */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-2 bg-white rounded-md border border-gray-200 text-center">
              <p className="text-xs text-gray-500 mb-0.5">OTW 비율</p>
              <p className="text-sm font-medium text-gray-900">{drilldown.otwPct.toFixed(1)}%</p>
            </div>
            <div className="p-2 bg-white rounded-md border border-gray-200 text-center">
              <p className="text-xs text-gray-500 mb-0.5">평균 연봉</p>
              <p className="text-sm font-medium text-gray-900">
                {drilldown.avgSalary != null
                  ? `${(drilldown.avgSalary / 10000).toFixed(0)}만원`
                  : '—'}
              </p>
            </div>
          </div>

          {/* Top companies */}
          {drilldown.topCompanies.length > 0 && (
            <>
              <p className="text-xs font-medium text-gray-700 mb-2">주요 채용 기업 (Top {drilldown.topCompanies.length})</p>
              <div className="flex flex-col gap-1 mb-4">
                {drilldown.topCompanies.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 px-2 py-1.5 bg-white rounded-md border border-gray-200 text-xs"
                  >
                    <span className="text-gray-400 w-4 text-right">{item.rank ?? i + 1}</span>
                    <span className="font-medium text-gray-900 flex-1">{item.company}</span>
                    <span className="text-gray-500">{item.count}건</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Weekly trend */}
          {drilldown.weeklyTrend.length > 0 && (
            <>
              <p className="text-xs font-medium text-gray-700 mb-2">주간 트렌드</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="text-gray-500">
                      <th className="text-left px-2 py-1 font-medium">주차</th>
                      <th className="text-right px-2 py-1 font-medium">수요</th>
                      <th className="text-right px-2 py-1 font-medium">공급</th>
                    </tr>
                  </thead>
                  <tbody>
                    {drilldown.weeklyTrend.map((row, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="px-2 py-1 text-gray-600">{row.week}</td>
                        <td className="px-2 py-1 text-right text-gray-900">{row.demand.toLocaleString()}</td>
                        <td className="px-2 py-1 text-right text-gray-900">{row.supply.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}

      {!isLoading && !drilldown && (
        <p className="text-xs text-gray-400 text-center py-4">드릴다운 데이터를 불러올 수 없습니다.</p>
      )}
    </div>
  )
}
