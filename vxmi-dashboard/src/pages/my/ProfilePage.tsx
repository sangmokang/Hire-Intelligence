import { useState } from 'react';
import { useAuthStore } from '../../stores/authStore';
import { apiClient } from '../../services/apiClient';
import type { UserRole, PlanType } from '../../types/auth';

const ROLE_LABEL: Record<UserRole, string> = {
  SUPER_ADMIN: '슈퍼 관리자',
  USER: '일반 사용자',
  GUEST: '게스트',
};

const PLAN_LABEL: Record<PlanType, string> = {
  TALENT_FREE: 'Talent 무료',
  TALENT_PLUS: 'Talent Plus',
  STARTER: 'Starter',
  PRO: 'Pro',
  ENTERPRISE: 'Enterprise',
};

const PLAN_COLOR: Record<PlanType, string> = {
  TALENT_FREE: 'bg-gray-100 text-gray-600',
  TALENT_PLUS: 'bg-blue-100 text-blue-700',
  STARTER: 'bg-green-100 text-green-700',
  PRO: 'bg-purple-100 text-purple-700',
  ENTERPRISE: 'bg-amber-100 text-amber-700',
};

export default function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [name, setName] = useState(user?.name ?? '');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (!user) return null;

  const joinDate = new Date(user.createdAt).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim() === user.name) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const { data } = await apiClient.patch('/api/v1/me', { name: name.trim() });
      setUser({ ...user, name: data.data.name });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      setSaveError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '저장에 실패했습니다.'
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">내 프로필</h1>
        <p className="text-sm text-gray-500 mt-1">계정 정보를 확인하고 수정하세요.</p>
      </div>

      {/* 기본 정보 카드 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-gray-900">기본 정보</h2>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-gray-500 mb-1">이메일</p>
            <p className="text-sm text-gray-800 font-medium">{user.email}</p>
          </div>

          <div className="flex gap-3">
            <div>
              <p className="text-xs text-gray-500 mb-1">역할</p>
              <span className="inline-block text-xs font-medium bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                {ROLE_LABEL[user.role]}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">플랜</p>
              <span className={`inline-block text-xs font-medium px-2 py-1 rounded-full ${PLAN_COLOR[user.plan]}`}>
                {PLAN_LABEL[user.plan]}
              </span>
            </div>
          </div>

          <div>
            <p className="text-xs text-gray-500 mb-1">가입일</p>
            <p className="text-sm text-gray-800">{joinDate}</p>
          </div>
        </div>
      </div>

      {/* 이름 수정 폼 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">이름 수정</h2>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              이름
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              placeholder="이름을 입력하세요"
              required
            />
          </div>

          {saveError && (
            <p className="text-sm text-red-600">{saveError}</p>
          )}
          {saveSuccess && (
            <p className="text-sm text-green-600">이름이 저장되었습니다.</p>
          )}

          <button
            type="submit"
            disabled={saving || name.trim() === user.name || name.trim() === ''}
            className="w-full sm:w-auto px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? '저장 중...' : '저장'}
          </button>
        </form>
      </div>
    </div>
  );
}
