import { useState } from 'react'
import logo from './assets/logo.svg'
import { SDMatrixView } from './components/views/SDMatrixView'
import { TopCompaniesView } from './components/views/TopCompaniesView'
import { CompanyTimelineView } from './components/views/CompanyTimelineView'
import { HiringTrendsView } from './components/views/HiringTrendsView'
import { ResumeMatchView } from './components/views/ResumeMatchView'
import { CompanyAnalysisView } from './components/views/CompanyAnalysisView'

const TABS = [
  { id: 'top-companies',    label: 'Top 20 채용 볼륨' },
  { id: 'sd-matrix',        label: '수요공급 매트릭스' },
  { id: 'company-timeline', label: '시계열 채용 인텔리전스' },
  { id: 'hiring-trends',    label: '채용 트렌드' },
  { id: 'resume-match',     label: '이력서 매칭' },
  { id: 'company-analysis', label: '기업 분석' },
]

function App() {
  const [activeTab, setActiveTab] = useState('top-companies')
  const [showLoginModal, setShowLoginModal] = useState(false)

  return (
    <div className="w-full min-h-screen flex flex-col px-6 py-8 md:px-12 lg:px-20">
      <div className="max-w-6xl mx-auto flex-1">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <img src={logo} alt="Value Connect" style={{ height: '36px' }} />
          <span className="text-lg font-medium text-gray-700">Hire Intelligence</span>
        </div>
        <button
          onClick={() => setShowLoginModal(true)}
          className="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors" style={{ backgroundColor: '#191918' }}
        >
          로그인
        </button>
      </div>

      {/* Tab Nav */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 pb-2 flex-wrap">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              activeTab === tab.id
                ? 'bg-gray-100 text-gray-900 font-medium'
                : 'text-gray-500 hover:bg-gray-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Panels */}
      {activeTab === 'sd-matrix'        && <SDMatrixView />}
      {activeTab === 'top-companies'    && <TopCompaniesView />}
      {activeTab === 'company-timeline' && <CompanyTimelineView />}
      {activeTab === 'hiring-trends'    && <HiringTrendsView />}
      {activeTab === 'resume-match'     && <ResumeMatchView />}
      {activeTab === 'company-analysis' && <CompanyAnalysisView />}
      </div>

      {/* Footer */}
      <footer style={{ backgroundColor: '#191918' }} className="mt-auto">
        <div className="max-w-6xl mx-auto px-6 md:px-12 lg:px-20 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Logo & Company */}
            <div>
              <img src={logo} alt="Value Connect" className="h-10 mb-4 brightness-200" />
              <p className="text-sm font-bold text-white tracking-wide">Value Connect</p>
              <p className="text-xs text-neutral-500 mt-2">채용 시장 인텔리전스 플랫폼</p>
            </div>

            {/* Products */}
            <div>
              <h4 className="text-sm font-bold text-white mb-4">Products</h4>
              <ul className="space-y-2.5">
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">채용 볼륨 분석</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">수요공급 매트릭스</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">시계열 인텔리전스</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">이력서 매칭</span></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-sm font-bold text-white mb-4">Resources</h4>
              <ul className="space-y-2.5">
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">채용 트렌드</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">기업 분석</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">API Documentation</span></li>
                <li><span className="text-sm text-neutral-400 hover:text-white transition-colors cursor-pointer">고객 지원</span></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-sm font-bold text-white mb-4">Company</h4>
              <ul className="space-y-2.5">
                <li><span className="text-sm text-neutral-400">밸류커넥트 주식회사</span></li>
                <li><span className="text-sm text-neutral-400">Since 2021</span></li>
                <li><a href="mailto:dev@valueconnect.kr" className="text-sm text-neutral-400 hover:text-white transition-colors">dev@valueconnect.kr</a></li>
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="mt-10 pt-6 border-t border-neutral-800 flex items-center justify-between">
            <span className="text-xs text-neutral-500">&copy; 2025 밸류커넥트 주식회사. All rights reserved.</span>
            <div className="flex items-center gap-4">
              <span className="text-xs text-neutral-500 hover:text-white transition-colors cursor-pointer">이용약관</span>
              <span className="text-xs text-neutral-500 hover:text-white transition-colors cursor-pointer">개인정보처리방침</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowLoginModal(false)}>
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm p-8" onClick={(e) => e.stopPropagation()}>
            {/* Close button */}
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>

            {/* Logo */}
            <div className="flex flex-col items-center mb-8">
              <img src={logo} alt="Value Connect" className="h-12 mb-3" />
              <h2 className="text-lg font-medium text-gray-900">로그인</h2>
              <p className="text-sm text-gray-500 mt-1">Value Connect에 오신 것을 환영합니다</p>
            </div>

            {/* Google Login */}
            <button className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors mb-3">
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

            {/* Email Login */}
            <div className="space-y-3">
              <input
                type="email"
                placeholder="이메일 주소"
                className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900"
              />
              <input
                type="password"
                placeholder="비밀번호"
                className="w-full px-4 py-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 text-gray-900"
              />
              <button className="w-full py-3 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors">
                이메일로 로그인
              </button>
            </div>

            {/* Sign up link */}
            <p className="text-center text-xs text-gray-500 mt-5">
              계정이 없으신가요?{' '}
              <button className="text-gray-900 font-medium hover:underline">회원가입</button>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
