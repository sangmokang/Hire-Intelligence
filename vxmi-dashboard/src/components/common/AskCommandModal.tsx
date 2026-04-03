/**
 * Expert Panel Cmd+K 커맨드 모달
 * Spotlight/Alfred 스타일 — 화면 중앙 상단, 반투명 오버레이
 */
import { useState, useRef, useEffect } from 'react';
import { useExpertPanelStore } from '../../stores/expertPanelStore';
import { ExpertBadge } from './ExpertBadge';

// 분류 축 라벨
const AXIS_LABEL: Record<string, string> = { TASK: '과업', FACT: '사실' };
const SPECIFICITY_LABEL: Record<string, string> = { AMBIGUOUS: '모호', CONCRETE: '구체' };

export function AskCommandModal() {
  const {
    isLoading, classification, responses, error,
    ask, sendFeedback, close, reset,
  } = useExpertPanelStore();
  const [input, setInput] = useState('');
  const [feedbackSent, setFeedbackSent] = useState<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement>(null);

  // 모달 열릴 때 input 포커스
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // ESC 키로 닫기
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close();
        reset();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [close, reset]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    // 현재 URL에서 view 추출
    const pathParts = window.location.pathname.split('/');
    const view = pathParts[pathParts.length - 1] || undefined;
    ask(input.trim(), view);
    setInput('');
    setFeedbackSent(new Set());
  };

  const handleFeedback = async (expertType: string, type: 'HELPFUL' | 'NOT_HELPFUL') => {
    await sendFeedback(expertType, type);
    setFeedbackSent((prev) => new Set(prev).add(`${expertType}_${type}`));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* 반투명 오버레이 */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => { close(); reset(); }}
      />

      {/* 모달 본체 */}
      <div className="relative w-full max-w-2xl mx-4 bg-white rounded-xl shadow-2xl overflow-hidden">
        {/* 입력 영역 */}
        <form onSubmit={handleSubmit} className="flex items-center border-b border-gray-200">
          <svg className="w-5 h-5 ml-4 text-gray-400 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="전문가에게 질문하세요... (예: 프론트엔드 채용 시장 동향은?)"
            className="flex-1 px-3 py-4 text-sm bg-transparent outline-none placeholder:text-gray-400"
            disabled={isLoading}
          />
          <kbd className="mr-4 px-2 py-1 rounded bg-gray-100 text-[10px] font-medium text-gray-500">
            ESC
          </kbd>
        </form>

        {/* 로딩 상태 */}
        {isLoading && (
          <div className="p-6 space-y-3">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-4 bg-gray-200 rounded w-2/3" />
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">전문가 분석 중...</p>
          </div>
        )}

        {/* 에러 */}
        {error && (
          <div className="p-4 bg-red-50 text-sm text-red-600">
            {error}
          </div>
        )}

        {/* 분류 결과 + 응답 */}
        {classification && !isLoading && (
          <div className="max-h-[60vh] overflow-y-auto">
            {/* 분류 배지 */}
            <div className="px-4 pt-3 pb-2 flex items-center gap-2 text-xs">
              <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-medium">
                {AXIS_LABEL[classification.axis] ?? classification.axis}
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">
                {SPECIFICITY_LABEL[classification.specificity] ?? classification.specificity}
              </span>
              <span className="text-gray-400">
                {classification.routingStrategy.replace(/_/g, ' ').toLowerCase()}
              </span>
            </div>

            {/* 전문가 응답 카드 */}
            <div className="p-4 space-y-3">
              {responses.map((resp) => (
                <div
                  key={resp.expert}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
                >
                  {/* 전문가 배지 */}
                  <div className="flex items-center justify-between mb-2">
                    <ExpertBadge expert={resp.expert} expertName={resp.expertName} />
                    <span className="text-xs text-gray-400">
                      {(resp.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* 답변 */}
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {resp.answer}
                  </p>

                  {/* 관련 뷰 */}
                  {resp.relatedViews.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {resp.relatedViews.slice(0, 3).map((v) => (
                        <span key={v} className="px-1.5 py-0.5 text-[10px] rounded bg-gray-100 text-gray-500">
                          {v}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 피드백 버튼 */}
                  <div className="mt-3 flex items-center gap-2 border-t border-gray-100 pt-2">
                    <button
                      onClick={() => handleFeedback(resp.expert, 'HELPFUL')}
                      disabled={feedbackSent.has(`${resp.expert}_HELPFUL`)}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                        feedbackSent.has(`${resp.expert}_HELPFUL`)
                          ? 'bg-green-100 text-green-700'
                          : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
                      }`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 01-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 00-1.302 4.665c0 1.194.232 2.333.654 3.375z" />
                      </svg>
                      {feedbackSent.has(`${resp.expert}_HELPFUL`) ? '감사합니다' : '도움됨'}
                    </button>
                    <button
                      onClick={() => handleFeedback(resp.expert, 'NOT_HELPFUL')}
                      disabled={feedbackSent.has(`${resp.expert}_NOT_HELPFUL`)}
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
                        feedbackSent.has(`${resp.expert}_NOT_HELPFUL`)
                          ? 'bg-red-100 text-red-700'
                          : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                      }`}
                    >
                      <svg className="w-3.5 h-3.5 rotate-180" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14.25 9h2.25M5.904 18.75c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 01-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 10.203 4.167 9.75 5 9.75h1.053c.472 0 .745.556.5.96a8.958 8.958 0 00-1.302 4.665c0 1.194.232 2.333.654 3.375z" />
                      </svg>
                      {feedbackSent.has(`${resp.expert}_NOT_HELPFUL`) ? '기록됨' : '아쉬움'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 하단 힌트 */}
        {!classification && !isLoading && !error && (
          <div className="px-4 py-3 text-xs text-gray-400 text-center">
            18명의 도메인 전문가가 대기 중입니다. 질문을 입력하고 Enter를 누르세요.
          </div>
        )}
      </div>
    </div>
  );
}
