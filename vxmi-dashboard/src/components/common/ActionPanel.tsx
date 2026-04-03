import { Link } from 'react-router-dom';
import type { ActionItem } from '../../types/action';

// ── Props ─────────────────────────────────────────────────────────────────────

export interface ActionPanelProps {
  insight: string;                                      // 1-2문장 데이터 해석
  actions: ActionItem[];                                // 1-3개 행동 권고
  relatedViews?: { label: string; path: string }[];    // 관련 뷰 링크
  isLocked?: boolean;                                   // Starter 플랜 잠금 여부
  isAiGenerated?: boolean;                              // Claude API 생성 여부
}

// ── Priority 색상 매핑 ──────────────────────────────────────────────────────

const PRIORITY_STYLES: Record<ActionItem['priority'], { badge: string; bar: string; label: string }> = {
  HIGH:   { badge: 'bg-red-100 text-red-700 border-red-200',    bar: 'bg-red-400',    label: '높음' },
  MEDIUM: { badge: 'bg-yellow-100 text-yellow-700 border-yellow-200', bar: 'bg-yellow-400', label: '중간' },
  LOW:    { badge: 'bg-green-100 text-green-700 border-green-200',  bar: 'bg-green-400',  label: '낮음' },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function PriorityBadge({ priority }: { priority: ActionItem['priority'] }) {
  const styles = PRIORITY_STYLES[priority];
  return (
    <span
      className={[
        'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border shrink-0',
        styles.badge,
      ].join(' ')}
    >
      {styles.label}
    </span>
  );
}

function ActionRow({ item }: { item: ActionItem }) {
  const styles = PRIORITY_STYLES[item.priority];
  return (
    <li className="flex flex-col gap-1.5">
      {/* 우선순위 바 + 텍스트 */}
      <div className="flex items-start gap-2">
        <div className={['mt-1.5 w-1 h-full min-h-[2rem] rounded-full shrink-0', styles.bar].join(' ')} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap mb-0.5">
            <PriorityBadge priority={item.priority} />
          </div>
          <p className="text-sm text-gray-700 leading-snug">{item.text}</p>
        </div>
      </div>
      {/* CTA 버튼 (선택적) */}
      {item.cta && item.ctaUrl && (
        <div className="pl-3">
          {item.ctaUrl.startsWith('/') ? (
            <Link
              to={item.ctaUrl}
              className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline transition-colors"
            >
              {item.cta}
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          ) : (
            <a
              href={item.ctaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline transition-colors"
            >
              {item.cta}
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
            </a>
          )}
        </div>
      )}
    </li>
  );
}

// ── Lock Overlay ──────────────────────────────────────────────────────────────

function LockOverlay() {
  return (
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 rounded-xl bg-white/70 backdrop-blur-sm">
      {/* 자물쇠 아이콘 */}
      <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
        </svg>
      </div>
      <div className="text-center px-4">
        <p className="text-sm font-semibold text-gray-800">AI 인사이트</p>
        <p className="text-xs text-gray-500 mt-0.5">Pro 플랜에서 AI 해석을 확인하세요</p>
      </div>
      <Link
        to="/my/billing"
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors shadow-sm"
      >
        Pro에서 AI 해석 보기
      </Link>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export function ActionPanel({ insight, actions, relatedViews, isLocked = false, isAiGenerated = false }: ActionPanelProps) {
  return (
    // 데스크탑: sticky 우측 패널 / 모바일: block (부모 레이아웃이 세로 스택 처리)
    <div className="relative bg-white border-l border-gray-200 shadow-sm flex flex-col gap-0 overflow-hidden">
      {/* 잠금 오버레이 */}
      {isLocked && <LockOverlay />}

      {/* 컨텐츠 — 잠김 시에도 blur로 배경에 렌더 */}
      <div className={isLocked ? 'blur-sm pointer-events-none select-none' : undefined}>
        {/* ── 인사이트 섹션 ── */}
        <section className="px-4 py-4 border-b border-gray-100">
          <h3 className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            <span>💡</span>
            <span>인사이트</span>
            {isAiGenerated && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
                AI
              </span>
            )}
          </h3>
          <p className="text-sm text-gray-700 leading-relaxed">{insight}</p>
        </section>

        {/* ── 추천 액션 섹션 ── */}
        {actions.length > 0 && (
          <section className="px-4 py-4 border-b border-gray-100">
            <h3 className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              <span>📋</span>
              <span>추천 액션</span>
            </h3>
            <ul className="space-y-3">
              {actions.map((item) => (
                <ActionRow key={`${item.priority}-${item.text.slice(0, 30)}`} item={item} />
              ))}
            </ul>
          </section>
        )}

        {/* ── 관련 뷰 섹션 ── */}
        {relatedViews && relatedViews.length > 0 && (
          <section className="px-4 py-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              관련 뷰
            </h3>
            <ul className="space-y-1">
              {relatedViews.map((view) => (
                <li key={view.path}>
                  <Link
                    to={view.path}
                    className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                  >
                    <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                    {view.label}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
