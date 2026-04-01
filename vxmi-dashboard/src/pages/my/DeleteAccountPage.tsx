import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { deleteAccount } from '../../services/userService';

type DeleteReason =
  | 'not_needed'
  | 'other_service'
  | 'privacy_concern'
  | 'other';

const REASONS: { value: DeleteReason; label: string }[] = [
  { value: 'not_needed', label: '더 이상 필요 없음' },
  { value: 'other_service', label: '다른 서비스 사용' },
  { value: 'privacy_concern', label: '개인정보 우려' },
  { value: 'other', label: '기타' },
];

export default function DeleteAccountPage() {
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  const [reason, setReason] = useState<DeleteReason | ''>('');
  const [password, setPassword] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canProceed = reason !== '' && password.length >= 1;

  const handleOpenModal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canProceed) return;
    setError(null);
    setShowModal(true);
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      await deleteAccount(password);
      await logout();
      navigate('/');
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? '계정 삭제에 실패했습니다. 다시 시도해 주세요.');
      setShowModal(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">회원 탈퇴</h1>
        <p className="text-sm text-gray-500 mt-1">계정을 삭제하면 모든 데이터가 영구적으로 제거됩니다.</p>
      </div>

      {/* 경고 배너 */}
      <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4">
        <svg
          className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div>
          <p className="text-sm font-medium text-red-800">이 작업은 되돌릴 수 없습니다</p>
          <p className="text-xs text-red-600 mt-0.5">
            계정 삭제 시 모든 분석 데이터, 저장된 설정, 구독 정보가 영구적으로 삭제됩니다.
          </p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-6">
        <form onSubmit={handleOpenModal} className="space-y-6">
          {/* 탈퇴 사유 선택 */}
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-3">탈퇴 사유</h2>
            <div className="space-y-2">
              {REASONS.map((r) => (
                <label
                  key={r.value}
                  className="flex items-center gap-3 cursor-pointer group"
                >
                  <input
                    type="radio"
                    name="reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="w-4 h-4 accent-gray-900"
                  />
                  <span className="text-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                    {r.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* 비밀번호 재입력 */}
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-3">비밀번호 확인</h2>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              현재 비밀번호를 입력하세요
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
              placeholder="비밀번호 입력"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={!canProceed}
            className="w-full sm:w-auto px-6 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            계정 삭제
          </button>
        </form>
      </div>

      {/* 확인 모달 */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-gray-900">계정 삭제 확인</h3>
            </div>
            <p className="text-sm text-gray-600">
              정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowModal(false)}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                취소
              </button>
              <button
                onClick={() => void handleConfirmDelete()}
                disabled={isDeleting}
                className="flex-1 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isDeleting ? '삭제 중...' : '삭제 확인'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
