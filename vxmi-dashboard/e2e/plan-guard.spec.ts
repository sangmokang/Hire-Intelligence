import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Plan Guard - Access Control', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
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
