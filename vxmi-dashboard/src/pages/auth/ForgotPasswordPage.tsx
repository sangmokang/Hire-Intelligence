import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { forgotPasswordSchema, type ForgotPasswordFormData } from '../../lib/validations';
import { authService } from '../../services/authService';
import logo from '../../assets/logo.svg';

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  async function onSubmit(values: ForgotPasswordFormData) {
    try {
      await authService.resetPassword(values.email);
      setSent(true);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '요청 처리 중 오류가 발생했습니다. 다시 시도해주세요.';
      setError('root', { message });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <img src={logo} alt="Value Connect" className="h-12 mb-3" />
          <h1 className="text-lg font-semibold text-gray-900">비밀번호 찾기</h1>
        </div>

        {sent ? (
          /* Success state */
          <div className="text-center">
            <div className="flex items-center justify-center w-12 h-12 bg-green-50 rounded-full mx-auto mb-4">
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-700 font-medium mb-1">이메일이 전송되었습니다.</p>
            <p className="text-sm text-gray-500">메일함을 확인해주세요.</p>
            <Link
              to="/login"
              className="inline-block mt-6 text-sm text-gray-900 font-medium hover:underline"
            >
              로그인으로 돌아가기
            </Link>
          </div>
        ) : (
          /* Form state */
          <>
            <p className="text-sm text-gray-500 text-center mb-6 leading-relaxed">
              가입한 이메일 주소를 입력하면 비밀번호 재설정 링크를 보내드립니다.
            </p>

            {errors.root && (
              <div className="mb-4 px-4 py-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600">
                {errors.root.message}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
              <div>
                <input
                  type="email"
                  placeholder="이메일 주소"
                  {...register('email')}
                  className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>
                )}
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ backgroundColor: '#191918' }}
              >
                {isSubmitting ? '전송 중...' : '재설정 링크 보내기'}
              </button>
            </form>

            <p className="text-center mt-5">
              <Link
                to="/login"
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                로그인으로 돌아가기
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
