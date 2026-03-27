import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../services/apiClient';

interface NotificationToggle {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

export default function SettingsPage() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState(false);

  const [notifications, setNotifications] = useState<NotificationToggle[]>([
    {
      id: 'weekly_report',
      label: '주간 리포트',
      description: '매주 월요일 채용 트렌드 요약 리포트를 이메일로 받습니다.',
      enabled: true,
    },
    {
      id: 'hiring_alert',
      label: '채용 알림',
      description: '관심 기업의 새 채용 공고가 등록되면 알림을 받습니다.',
      enabled: false,
    },
  ]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPwError('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    if (newPassword.length < 8) {
      setPwError('비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    setPwLoading(true);
    setPwError(null);
    setPwSuccess(false);
    try {
      await apiClient.post('/api/v1/me/password', {
        currentPassword,
        newPassword,
      });
      setPwSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPwSuccess(false), 3000);
    } catch (err: unknown) {
      setPwError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? '비밀번호 변경에 실패했습니다.'
      );
    } finally {
      setPwLoading(false);
    }
  };

  const toggleNotification = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, enabled: !n.enabled } : n))
    );
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">설정</h1>
        <p className="text-sm text-gray-500 mt-1">계정 보안 및 알림을 관리하세요.</p>
      </div>

      {/* 비밀번호 변경 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">비밀번호 변경</h2>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
              현재 비밀번호
            </label>
            <input
              id="currentPassword"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              placeholder="현재 비밀번호"
              required
            />
          </div>
          <div>
            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
              새 비밀번호
            </label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              placeholder="새 비밀번호 (8자 이상)"
              required
            />
          </div>
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
              새 비밀번호 확인
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              placeholder="새 비밀번호 재입력"
              required
            />
          </div>

          {pwError && <p className="text-sm text-red-600">{pwError}</p>}
          {pwSuccess && <p className="text-sm text-green-600">비밀번호가 변경되었습니다.</p>}

          <button
            type="submit"
            disabled={pwLoading}
            className="w-full sm:w-auto px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {pwLoading ? '변경 중...' : '비밀번호 변경'}
          </button>
        </form>
      </div>

      {/* 알림 설정 */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">알림 설정</h2>
        <div className="space-y-4">
          {notifications.map((notif) => (
            <div key={notif.id} className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{notif.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{notif.description}</p>
              </div>
              <button
                onClick={() => toggleNotification(notif.id)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none ${
                  notif.enabled ? 'bg-gray-900' : 'bg-gray-200'
                }`}
                role="switch"
                aria-checked={notif.enabled}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ${
                    notif.enabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* 위험 구역 */}
      <div className="bg-white border border-red-200 rounded-xl p-6">
        <h2 className="text-base font-semibold text-red-600 mb-2">위험 구역</h2>
        <p className="text-sm text-gray-500 mb-4">
          계정을 탈퇴하면 모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
        </p>
        <Link
          to="/my/delete-account"
          className="inline-block px-4 py-2 border border-red-300 text-red-600 text-sm font-medium rounded-lg hover:bg-red-50 transition-colors"
        >
          회원 탈퇴
        </Link>
      </div>
    </div>
  );
}
