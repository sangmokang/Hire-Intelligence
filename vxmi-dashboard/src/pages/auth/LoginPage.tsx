import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, type LoginFormData } from '../../lib/validations';
import { authService } from '../../services/authService';
import { useAuthStore } from '../../stores/authStore';
import { trackEvent } from '../../lib/analytics';
import logo from '../../assets/logo.svg';

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { rememberMe: false },
  });

  async function onSubmit(values: LoginFormData) {
    try {
      await login({ email: values.email, password: values.password, rememberMe: values.rememberMe });
      trackEvent('Auth', 'login_success', 'email');
      navigate('/dashboard');
    } catch (err: unknown) {
      // authStore가 이미 error state에 파싱된 메시지를 저장함
      const storeError = useAuthStore.getState().error;
      const message = storeError
        || (err instanceof Error ? err.message : '로그인에 실패했습니다. 다시 시도해주세요.');
      setError('root', { message });
    }
  }

  async function handleGoogleLogin() {
    try {
      await authService.signInWithGoogle();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Google 로그인에 실패했습니다.';
      setError('root', { message });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <img src={logo} alt="Value Connect" className="h-12 mb-3" />
          <h1 className="text-lg font-semibold text-gray-900">로그인</h1>
          <p className="text-sm text-gray-500 mt-1">Value Connect에 오신 것을 환영합니다</p>
        </div>

        {/* Google OAuth */}
        <button
          type="button"
          onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors mb-3"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          <span className="text-sm text-gray-700 font-medium">Google로 계속하기</span>
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">또는</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Root error */}
        {errors.root && (
          <div className="mb-4 px-4 py-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600">
            {errors.root.message}
          </div>
        )}

        {/* Form */}
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

          <div>
            <input
              type="password"
              placeholder="비밀번호"
              {...register('password')}
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          {/* Remember me + Forgot password */}
          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                {...register('rememberMe')}
                className="w-4 h-4 rounded border-gray-300 accent-gray-900"
              />
              <span className="text-sm text-gray-600">로그인 상태 유지</span>
            </label>
            <Link
              to="/forgot-password"
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              비밀번호 찾기
            </Link>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#191918' }}
          >
            {isSubmitting ? '로그인 중...' : '이메일로 로그인'}
          </button>
        </form>

        {/* Register link */}
        <p className="text-center text-xs text-gray-500 mt-5">
          계정이 없으신가요?{' '}
          <Link to="/register" className="text-gray-900 font-medium hover:underline">
            회원가입
          </Link>
        </p>
      </div>
    </div>
  );
}
