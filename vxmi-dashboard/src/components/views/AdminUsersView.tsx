import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchAdminUsers,
  type AdminUserDetail,
  type AdminUserListParams,
} from '../../services/adminApi'

// 날짜 포맷 헬퍼
function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}

// 역할 배지 색상
function RoleBadge({ role }: { role: string }) {
  const colorMap: Record<string, string> = {
    SUPER_ADMIN: 'bg-purple-100 text-purple-700',
    ADMIN: 'bg-blue-100 text-blue-700',
    USER: 'bg-gray-100 text-gray-600',
  }
  const labelMap: Record<string, string> = {
    SUPER_ADMIN: '슈퍼어드민',
    ADMIN: '어드민',
    USER: '사용자',
  }
  const cls = colorMap[role] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {labelMap[role] ?? role}
    </span>
  )
}

// 상태 배지 색상
function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    ACTIVE: 'bg-green-100 text-green-700',
    INACTIVE: 'bg-gray-100 text-gray-500',
    BLOCKED: 'bg-red-100 text-red-700',
    SUSPENDED: 'bg-orange-100 text-orange-700',
  }
  const labelMap: Record<string, string> = {
    ACTIVE: '활성',
    INACTIVE: '비활성',
    BLOCKED: '차단',
    SUSPENDED: '정지',
  }
  const cls = colorMap[status] ?? 'bg-gray-100 text-gray-500'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {labelMap[status] ?? status}
    </span>
  )
}

const LIMIT = 20

export function AdminUsersView() {
  const navigate = useNavigate()

  // 필터 상태
  const [roleFilter, setRoleFilter] = useState('')
  const [planFilter, setPlanFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [offset, setOffset] = useState(0)

  // 데이터 상태
  const [users, setUsers] = useState<AdminUserDetail[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 필터 변경 시 offset 초기화
  useEffect(() => {
    setOffset(0)
  }, [roleFilter, planFilter, statusFilter])

  // 유저 목록 조회
  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    const params: AdminUserListParams = { offset, limit: LIMIT }
    if (roleFilter) params.role = roleFilter
    if (planFilter) params.plan = planFilter
    if (statusFilter) params.status = statusFilter

    fetchAdminUsers(params)
      .then((res) => {
        if (!cancelled) {
          setUsers(res.users)
          setTotal(res.total)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : '데이터를 불러오지 못했습니다.')
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => { cancelled = true }
  }, [offset, roleFilter, planFilter, statusFilter])

  const totalPages = Math.ceil(total / LIMIT)
  const currentPage = Math.floor(offset / LIMIT) + 1

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">유저 관리</h1>
        <p className="text-sm text-gray-500 mt-0.5">전체 사용자 목록 조회 및 관리</p>
      </div>

      {/* 필터 바 */}
      <div className="flex flex-wrap items-center gap-3 mb-4 p-3 bg-gray-50 rounded-xl border border-gray-200">
        {/* 역할 필터 */}
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">역할</span>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
          >
            <option value="">전체</option>
            <option value="USER">USER</option>
            <option value="ADMIN">ADMIN</option>
            <option value="SUPER_ADMIN">SUPER_ADMIN</option>
          </select>
        </div>

        {/* 플랜 필터 */}
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">플랜</span>
          <select
            value={planFilter}
            onChange={(e) => setPlanFilter(e.target.value)}
            className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
          >
            <option value="">전체</option>
            <option value="STARTER">STARTER</option>
            <option value="PRO">PRO</option>
            <option value="ENTERPRISE">ENTERPRISE</option>
          </select>
        </div>

        {/* 상태 필터 */}
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">상태</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs px-2 py-1.5 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
          >
            <option value="">전체</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>
        </div>

        {/* 초기화 버튼 */}
        {(roleFilter || planFilter || statusFilter) && (
          <button
            onClick={() => { setRoleFilter(''); setPlanFilter(''); setStatusFilter('') }}
            className="mt-4 text-xs px-3 py-1.5 bg-white border border-gray-200 text-gray-500 rounded-md hover:bg-gray-100 transition-colors"
          >
            초기화
          </button>
        )}

        <div className="ml-auto text-xs text-gray-400 mt-4">
          총 {total.toLocaleString()}명
        </div>
      </div>

      {/* 에러 */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* 테이블 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">이메일</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">이름</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">역할</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">플랜</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">상태</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">마지막 로그인</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500">가입일</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                // 로딩 스켈레톤
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-100 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-sm text-gray-400">
                    조회된 사용자가 없습니다.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.userId}
                    onClick={() => navigate(`/admin/users/${user.userId}`)}
                    className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-gray-900 font-medium">{user.email ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-700">{user.name ?? '—'}</td>
                    <td className="px-4 py-3"><RoleBadge role={user.role} /></td>
                    <td className="px-4 py-3 text-gray-600 text-xs">{user.plan}</td>
                    <td className="px-4 py-3"><StatusBadge status={user.status} /></td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(user.lastLoginAt)}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(user.createdAt)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              {currentPage} / {totalPages} 페이지
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                disabled={offset === 0}
                className="text-xs px-3 py-1.5 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                이전
              </button>
              <button
                onClick={() => setOffset(offset + LIMIT)}
                disabled={offset + LIMIT >= total}
                className="text-xs px-3 py-1.5 border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                다음
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
