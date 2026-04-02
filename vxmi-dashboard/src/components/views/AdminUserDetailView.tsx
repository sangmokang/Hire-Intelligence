import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  fetchAdminUserDetail,
  updateAdminUser,
  type AdminUserDetail,
  type AdminUserUpdateRequest,
} from '../../services/adminApi'
import { useAuthStore } from '../../stores/authStore'

// 날짜 포맷 헬퍼
function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 정보 행 컴포넌트
function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center gap-4 py-2 border-b border-gray-50 last:border-0">
      <span className="w-32 shrink-0 text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-900">{value ?? '—'}</span>
    </div>
  )
}

export function AdminUserDetailView() {
  const { id: userId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const currentUser = useAuthStore((s) => s.user)

  // 유저 데이터 상태
  const [user, setUser] = useState<AdminUserDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)

  // 편집 폼 상태
  const [editRole, setEditRole] = useState('')
  const [editStatus, setEditStatus] = useState('')
  const [editPlan, setEditPlan] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // 현재 로그인 사용자와 동일 여부 — 자기 자신의 역할 변경 방지
  const isSelf = currentUser?.id === userId

  useEffect(() => {
    if (!userId) return
    let cancelled = false
    setIsLoading(true)
    setFetchError(null)

    fetchAdminUserDetail(userId)
      .then((data) => {
        if (!cancelled) {
          setUser(data)
          setEditRole(data.role)
          setEditStatus(data.status)
          setEditPlan(data.plan)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setFetchError(err instanceof Error ? err.message : '사용자 정보를 불러오지 못했습니다.')
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => { cancelled = true }
  }, [userId])

  async function handleSave() {
    if (!userId || !user) return
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    const payload: AdminUserUpdateRequest = {}
    // 변경된 항목만 전송
    if (editRole !== user.role) payload.role = editRole
    if (editStatus !== user.status) payload.status = editStatus
    if (editPlan !== user.plan) payload.plan = editPlan

    if (Object.keys(payload).length === 0) {
      setIsSaving(false)
      setSaveSuccess(true)
      return
    }

    try {
      const updated = await updateAdminUser(userId, payload)
      setUser(updated)
      setEditRole(updated.role)
      setEditStatus(updated.status)
      setEditPlan(updated.plan)
      setSaveSuccess(true)
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : '저장에 실패했습니다.')
    } finally {
      setIsSaving(false)
    }
  }

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-100 rounded w-48" />
          <div className="h-4 bg-gray-100 rounded w-32" />
          <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-4 bg-gray-100 rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  // 에러 상태
  if (fetchError) {
    return (
      <div className="p-6">
        <button
          onClick={() => navigate('/admin/users')}
          className="mb-4 text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
        >
          ← 목록으로
        </button>
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {fetchError}
        </div>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="p-6 max-w-3xl">
      {/* 헤더 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/admin/users')}
          className="mb-3 text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors"
        >
          ← 목록으로
        </button>
        <h1 className="text-xl font-semibold text-gray-900">유저 상세</h1>
        <p className="text-sm text-gray-500 mt-0.5">{user.email}</p>
      </div>

      <div className="space-y-5">
        {/* 기본 정보 카드 */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-3">기본 정보</h2>
          <InfoRow label="유저 ID" value={<span className="font-mono text-xs text-gray-600">{user.userId}</span>} />
          <InfoRow label="이메일" value={user.email} />
          <InfoRow label="이름" value={user.name} />
          <InfoRow label="회사" value={user.company} />
          <InfoRow label="직함" value={user.jobTitle} />
          <InfoRow label="로그인 횟수" value={`${user.loginCount.toLocaleString()}회`} />
          <InfoRow label="마지막 로그인" value={formatDate(user.lastLoginAt)} />
          <InfoRow label="가입일" value={formatDate(user.createdAt)} />
        </div>

        {/* 구독 정보 카드 */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-3">구독 정보</h2>
          <InfoRow label="구독 플랜" value={user.subscriptionPlan} />
          <InfoRow label="구독 상태" value={user.subscriptionStatus} />
          <InfoRow label="구독 시작" value={formatDate(user.subscriptionStartedAt)} />
          <InfoRow label="구독 만료" value={formatDate(user.subscriptionExpiresAt)} />
        </div>

        {/* 편집 카드 */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-3">관리자 설정</h2>

          <div className="space-y-4">
            {/* 역할 변경 — 자기 자신은 변경 불가 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">역할</label>
              {isSelf ? (
                <div className="flex items-center gap-2">
                  <select
                    value={editRole}
                    disabled
                    className="text-sm px-3 py-2 border border-gray-200 rounded-md bg-gray-50 text-gray-400 cursor-not-allowed"
                  >
                    <option value={editRole}>{editRole}</option>
                  </select>
                  <span className="text-xs text-amber-600">자기 자신의 역할은 변경할 수 없습니다.</span>
                </div>
              ) : (
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value)}
                  className="text-sm px-3 py-2 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
                >
                  <option value="USER">USER</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                </select>
              )}
            </div>

            {/* 상태 변경 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">상태</label>
              <select
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value)}
                className="text-sm px-3 py-2 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="SUSPENDED">SUSPENDED</option>
                <option value="INACTIVE">INACTIVE</option>
                <option value="BLOCKED">BLOCKED</option>
              </select>
            </div>

            {/* 플랜 변경 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">플랜</label>
              <select
                value={editPlan}
                onChange={(e) => setEditPlan(e.target.value)}
                className="text-sm px-3 py-2 border border-gray-200 rounded-md bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="STARTER">STARTER</option>
                <option value="PRO">PRO</option>
                <option value="ENTERPRISE">ENTERPRISE</option>
              </select>
            </div>
          </div>

          {/* 피드백 메시지 */}
          {saveError && (
            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-600">
              {saveError}
            </div>
          )}
          {saveSuccess && (
            <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-700">
              저장되었습니다.
            </div>
          )}

          {/* 저장 버튼 */}
          <div className="mt-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-gray-900 text-white text-sm rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? '저장 중...' : '저장'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
