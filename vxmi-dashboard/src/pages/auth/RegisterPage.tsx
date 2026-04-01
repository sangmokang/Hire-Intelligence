import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, type RegisterFormData } from '../../lib/validations';
import { useAuthStore } from '../../stores/authStore';
import logo from '../../assets/logo.svg';
import type { UserCategory } from '../../types/auth';

const CATEGORIES: { value: UserCategory; label: string }[] = [
  { value: 'JOB_SEEKER', label: '구직자' },
  { value: 'INHOUSE_HR', label: '인하우스 HR (기업 채용담당)' },
  { value: 'HEADHUNTER', label: '헤드헌터 (서치펌/에이전시)' },
  { value: 'CHRO', label: 'CHRO (최고인사책임자)' },
];

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register: storeRegister } = useAuthStore();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { category: 'JOB_SEEKER' },
  });

  const category = watch('category');
  const requiresCompany = category === 'INHOUSE_HR' || category === 'HEADHUNTER' || category === 'CHRO';

  async function onSubmit(values: RegisterFormData) {
    try {
      await storeRegister({
        name: values.name,
        email: values.email,
        password: values.password,
        category: values.category,
        company: values.company,
      });
      navigate('/dashboard');
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : '회원가입에 실패했습니다. 다시 시도해주세요.';
      setError('root', { message });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <img src={logo} alt="Value Connect" className="h-12 mb-3" />
          <h1 className="text-lg font-semibold text-gray-900">회원가입</h1>
          <p className="text-sm text-gray-500 mt-1">채용 시장 인텔리전스를 시작하세요</p>
        </div>

        {/* Root error */}
        {errors.root && (
          <div className="mb-4 px-4 py-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600">
            {errors.root.message}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <input
              type="text"
              placeholder="이름"
              {...register('name')}
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>
            )}
          </div>

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
              placeholder="비밀번호 (8자 이상, 대문자·숫자 포함)"
              {...register('password')}
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div>
            <input
              type="password"
              placeholder="비밀번호 확인"
              {...register('confirmPassword')}
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-red-500">{errors.confirmPassword.message}</p>
            )}
          </div>

          {/* Category */}
          <div className="pt-1">
            <p className="text-xs font-medium text-gray-600 mb-2">회원 유형</p>
            <div className="space-y-2">
              {CATEGORIES.map((cat) => (
                <label key={cat.value} className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="radio"
                    value={cat.value}
                    {...register('category')}
                    className="w-4 h-4 border-gray-300 accent-gray-900"
                  />
                  <span className="text-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                    {cat.label}
                  </span>
                </label>
              ))}
            </div>
            {errors.category && (
              <p className="mt-1 text-xs text-red-500">{errors.category.message}</p>
            )}
          </div>

          {/* Company - conditional */}
          {requiresCompany && (
            <div>
              <input
                type="text"
                placeholder="회사/기관명"
                {...register('company')}
                className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900 placeholder-gray-400"
              />
              {errors.company && (
                <p className="mt-1 text-xs text-red-500">{errors.company.message}</p>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            style={{ backgroundColor: '#191918' }}
          >
            {isSubmitting ? '처리 중...' : '회원가입'}
          </button>
        </form>

        {/* Login link */}
        <p className="text-center text-xs text-gray-500 mt-5">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="text-gray-900 font-medium hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  );
}
