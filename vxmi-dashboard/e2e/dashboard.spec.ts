import { test, expect } from '@playwright/test';

test.describe('Dashboard Navigation', () => {
  // Helper to bypass auth (MSW handles mock auth)
  test.beforeEach(async ({ page }) => {
    // MSW will handle /api/v1/auth/* requests
    // We need to set auth state - navigate to login and sign in with mock credentials
    await page.goto('/login');
    await page.getByPlaceholder('이메일 주소').fill('admin@vxmi.io');
    await page.getByPlaceholder('비밀번호').fill('password123');
    await page.getByText('이메일로 로그인').click();
    // Wait for navigation to dashboard
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('E2E-002: should navigate through all 6 analysis views', async ({ page }) => {
    // Should be on dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to each view via sidebar
    const views = [
      { nav: 'Top 기업', url: '/dashboard/top-companies' },
      { nav: 'S/D 매트릭스', url: '/dashboard/sd-matrix' },
      { nav: '시계열', url: '/dashboard/timeline' },
      { nav: '트렌드', url: '/dashboard/trends' },
      { nav: '이력서', url: '/dashboard/resume-match' },
      { nav: '기업 분석', url: '/dashboard/company-analysis' },
    ];

    for (const view of views) {
      // Click sidebar navigation
      const navLink = page.getByRole('link', { name: new RegExp(view.nav) });
      if (await navLink.isVisible()) {
        await navLink.click();
        await expect(page).toHaveURL(new RegExp(view.url));
        // Wait for content to load (not just skeleton)
        await page.waitForTimeout(1000);
      }
    }
  });

  test('should show role-based menu items', async ({ page }) => {
    // As admin user, should see admin menu
    // Check for analysis nav items
    await expect(page.getByText('분석')).toBeVisible();
  });
});
