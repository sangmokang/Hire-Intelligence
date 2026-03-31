import { test, expect } from '@playwright/test';

test.describe('Plan Guard - Access Control', () => {
  test.beforeEach(async ({ page }) => {
    // MSW mock 환경에서 로그인
    await page.goto('/login');
    await page.getByPlaceholder('이메일 주소').fill('admin@vxmi.io');
    await page.getByPlaceholder('비밀번호').fill('password123');
    await page.getByText('이메일로 로그인').click();
    await page.waitForURL(/\/dashboard/, { timeout: 10000 });
  });

  test('E2E-PG01: should access top-companies without plan restriction', async ({ page }) => {
    await page.goto('/dashboard/top-companies');
    await expect(page).toHaveURL(/\/dashboard\/top-companies/);
    // PlanGuard 메시지가 안 보여야 함
    await expect(page.getByText('플랜 전용 기능')).not.toBeVisible();
  });

  test('E2E-PG02: should access sd-matrix without plan restriction', async ({ page }) => {
    await page.goto('/dashboard/sd-matrix');
    await expect(page).toHaveURL(/\/dashboard\/sd-matrix/);
  });
});
