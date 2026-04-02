import type { ReactNode } from 'react';
import { ActionPanel } from './ActionPanel';
import type { ActionPanelProps } from './ActionPanel';

interface ActionPanelLayoutProps {
  children: ReactNode;     // 메인 컨텐츠 (66% 너비)
  panel: ActionPanelProps; // ActionPanel에 전달할 props
}

/**
 * ActionPanelLayout
 * - 데스크탑: children(66%) | ActionPanel(34%) 가로 배치
 * - 모바일(<768px): children → ActionPanel 세로 스택
 */
export function ActionPanelLayout({ children, panel }: ActionPanelLayoutProps) {
  return (
    // 모바일: flex-col / 데스크탑: flex-row, 높이 전체 사용
    <div className="flex flex-col md:flex-row min-h-full">
      {/* 메인 컨텐츠 — 66% */}
      <div className="flex-1 md:w-[66%] min-w-0 overflow-y-auto">
        {children}
      </div>

      {/* 액션 패널 — 34%, 데스크탑에서 sticky */}
      <div className="w-full md:w-[34%] md:sticky md:top-0 md:self-start md:max-h-screen md:overflow-y-auto shrink-0">
        <ActionPanel {...panel} />
      </div>
    </div>
  );
}
