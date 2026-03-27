import { Navigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function LandingPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen scroll-smooth">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#191918]/95 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <span className="text-[#191918] font-bold text-sm">V</span>
              </div>
              <span className="text-white font-bold text-lg tracking-tight">ValueHire</span>
            </div>

            {/* Nav links */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-white/70 hover:text-white text-sm transition-colors">기능</a>
              <a href="#pricing" className="text-white/70 hover:text-white text-sm transition-colors">요금제</a>
            </div>

            {/* CTA buttons */}
            <div className="flex items-center gap-3">
              <Link
                to="/login"
                className="text-white/80 hover:text-white text-sm px-4 py-2 rounded-lg border border-white/20 hover:border-white/40 transition-all"
              >
                로그인
              </Link>
              <Link
                to="/register"
                className="bg-white text-[#191918] text-sm font-semibold px-4 py-2 rounded-lg hover:bg-white/90 transition-all"
              >
                무료 시작
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-[#191918] pt-32 pb-24 relative overflow-hidden">
        {/* Abstract background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
          <div className="absolute top-1/2 -left-20 w-64 h-64 bg-white/3 rounded-full blur-2xl" />
          <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-white/4 rounded-full blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 mb-8">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-white/80 text-xs font-medium">주간 데이터 갱신 중</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
              채용 시장의<br />
              <span className="text-white/60">수요와 공급을</span><br />
              한눈에
            </h1>

            <p className="text-white/60 text-lg sm:text-xl leading-relaxed mb-10 max-w-2xl mx-auto">
              데이터 기반 채용 인텔리전스로 더 똑똑한 HR 의사결정을 시작하세요
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/register"
                className="w-full sm:w-auto bg-white text-[#191918] font-semibold px-8 py-3.5 rounded-xl hover:bg-white/90 transition-all text-base"
              >
                무료로 시작하기
              </Link>
              <a
                href="#features"
                className="w-full sm:w-auto border border-white/30 text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-white/10 transition-all text-base"
              >
                데모 살펴보기
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-[#111110] border-y border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { value: '14개', label: '직군 분석' },
              { value: '50+', label: '기업 추적' },
              { value: '주간', label: '데이터 갱신' },
              { value: '실시간', label: '수요공급 분석' },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col items-center gap-1">
                <span className="text-white font-bold text-xl">{stat.value}</span>
                <span className="text-white/50 text-sm">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              채용 시장을 입체적으로 분석하세요
            </h2>
            <p className="text-gray-500 text-lg max-w-2xl mx-auto">
              4가지 핵심 인텔리전스 뷰로 채용 시장의 흐름을 파악하세요
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6.75v6.75" />
                  </svg>
                ),
                title: '수요공급 매트릭스',
                desc: '직군별 채용 수요/공급 비율을 버블 차트로 시각화하여 시장 포지션을 한눈에 파악합니다.',
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 7.5L7.5 3m0 0L12 7.5M7.5 3v13.5m13.5 0L16.5 21m0 0L12 16.5m4.5 4.5V7.5" />
                  </svg>
                ),
                title: 'Top 채용 기업 순위',
                desc: '주간 채용 활동 상위 기업 랭킹과 전주 대비 변화를 실시간으로 추적합니다.',
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                  </svg>
                ),
                title: '시계열 인텔리전스',
                desc: '기업별 채용 트렌드 12주 추이를 분석하여 채용 패턴과 사이클을 파악합니다.',
              },
              {
                icon: (
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
                  </svg>
                ),
                title: '채용 트렌드',
                desc: '직군별 채용 시장 변화를 한눈에 추적하여 미래 채용 전략을 수립합니다.',
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="group bg-gray-50 hover:bg-[#191918] rounded-2xl p-6 transition-all duration-300 cursor-default"
              >
                <div className="w-12 h-12 bg-white group-hover:bg-white/10 rounded-xl flex items-center justify-center mb-4 text-[#191918] group-hover:text-white transition-colors shadow-sm">
                  {feature.icon}
                </div>
                <h3 className="font-semibold text-gray-900 group-hover:text-white mb-2 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-500 group-hover:text-white/60 text-sm leading-relaxed transition-colors">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              합리적인 가격으로 시작하세요
            </h2>
            <p className="text-gray-500 text-lg">
              팀 규모와 목적에 맞는 플랜을 선택하세요
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Starter */}
            <div className="bg-white rounded-2xl p-8 border border-gray-100 flex flex-col">
              <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-900 mb-1">Starter</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-gray-900">무료</span>
                </div>
                <p className="text-gray-500 text-sm mt-2">기본 시장 데이터로 시작하세요</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {['기본 시장 데이터', 'SD Matrix 뷰', 'Top Companies 순위'].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="w-full text-center py-3 rounded-xl border border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-all"
              >
                무료로 시작
              </Link>
            </div>

            {/* Pro (highlighted) */}
            <div className="bg-[#191918] rounded-2xl p-8 flex flex-col relative ring-2 ring-[#191918]">
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                <span className="bg-white text-[#191918] text-xs font-bold px-3 py-1 rounded-full">인기</span>
              </div>
              <div className="mb-6">
                <h3 className="text-lg font-bold text-white mb-1">Pro</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">₩49,000</span>
                  <span className="text-white/50 text-sm">/월</span>
                </div>
                <p className="text-white/50 text-sm mt-2">전문 HR 분석가를 위한 풀 액세스</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {['전체 분석 뷰 무제한', '드릴다운 인터랙션', '트렌드 12주 추이', '주간 리포트 이메일'].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-white/80">
                    <svg className="w-4 h-4 text-white/60 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/register"
                className="w-full text-center py-3 rounded-xl bg-white text-[#191918] font-semibold text-sm hover:bg-white/90 transition-all"
              >
                Pro 시작하기
              </Link>
            </div>

            {/* Enterprise */}
            <div className="bg-white rounded-2xl p-8 border border-gray-100 flex flex-col">
              <div className="mb-6">
                <h3 className="text-lg font-bold text-gray-900 mb-1">Enterprise</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-gray-900">₩149,000</span>
                  <span className="text-gray-400 text-sm">/월</span>
                </div>
                <p className="text-gray-500 text-sm mt-2">대규모 팀을 위한 맞춤 솔루션</p>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {['맞춤 리포트 제작', 'API 액세스', '전담 고객 지원', '커스텀 인테그레이션'].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
                    <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
              <a
                href="mailto:contact@valuehire.cc"
                className="w-full text-center py-3 rounded-xl border border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-all"
              >
                문의하기
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#191918] py-12 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-white rounded-lg flex items-center justify-center">
                <span className="text-[#191918] font-bold text-xs">V</span>
              </div>
              <span className="text-white/80 text-sm">© 2026 ValueHire. All rights reserved.</span>
            </div>
            <div className="flex items-center gap-6">
              {[
                { label: '서비스 소개', href: '#features' },
                { label: '요금제', href: '#pricing' },
                { label: '개인정보처리방침', href: '#' },
                { label: '이용약관', href: '#' },
              ].map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-white/50 hover:text-white/80 text-sm transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
