import ReactGA from 'react-ga4';

const GA4_MEASUREMENT_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID;

// GA4 초기화 여부 추적
let initialized = false;

/**
 * GA4 초기화 — VITE_GA4_MEASUREMENT_ID 환경 변수가 없으면 조용히 스킵
 */
export function initGA4() {
  if (!GA4_MEASUREMENT_ID) {
    // 측정 ID 미설정 시 초기화 생략 (개발 환경 등)
    return;
  }

  ReactGA.initialize(GA4_MEASUREMENT_ID);
  initialized = true;
}

/**
 * 페이지뷰 이벤트 전송
 * @param path - 현재 경로 (예: /dashboard/top-companies)
 * @param title - 페이지 제목 (옵션)
 */
export function trackPageView(path: string, title?: string) {
  if (!initialized) return;

  ReactGA.send({
    hitType: 'pageview',
    page: path,
    title: title,
  });
}

/**
 * 커스텀 이벤트 전송
 * @param category - 이벤트 카테고리 (예: 'Navigation', 'Auth')
 * @param action - 이벤트 액션 (예: 'click_sidebar_nav', 'login_success')
 * @param label - 이벤트 라벨 (옵션, 예: 메뉴 이름)
 */
export function trackEvent(category: string, action: string, label?: string) {
  if (!initialized) return;

  ReactGA.event({
    category,
    action,
    label,
  });
}
