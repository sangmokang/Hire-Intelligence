import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('E2E-002: should navigate through analysis views', async ({ page }) => {
    await expect(page).toHaveURL(/\/dashboard/);

    const views = [
      { nav: 'Top 기업', url: '/dashboard/top-companies' },
      { nav: 'S/D 매트릭스', url: '/dashboard/sd-matrix' },
      { nav: '시계열', url: '/dashboard/timeline' },
      { nav: '트렌드', url: '/dashboard/trends' },
      { nav: '이력서', url: '/dashboard/resume-match' },
      { nav: '기업 분석', url: '/dashboard/company-analysis' },
    ];

    for (const view of views) {
      const navLink = page.getByRole('link', { name: new RegExp(view.nav) });
      if (await navLink.isVisible()) {
        await navLink.click();
        await expect(page).toHaveURL(new RegExp(view.url));
        await page.waitForTimeout(500);
      }
    }
  });

  test('should show role-based menu items', async ({ page }) => {
    // 사이드바 섹션 헤더가 표시되는지 확인 (exact match로 다른 '분석' 포함 텍스트 제외)
    await expect(page.getByText('분석', { exact: true })).toBeVisible();
  });
});
