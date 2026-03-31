import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test('E2E-L01: should display landing page at root URL', async ({ page }) => {
    await page.goto('/');
    // 비인증 상태에서 랜딩 페이지 표시
    await expect(page.getByText('ValueHire')).toBeVisible();
  });

  test('E2E-L02: should have login link', async ({ page }) => {
    await page.goto('/');
    const loginLink = page.getByRole('link', { name: '로그인' });
    await expect(loginLink).toBeVisible();
    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('E2E-L03: should have register CTA', async ({ page }) => {
    await page.goto('/');
    const registerLink = page.getByRole('link', { name: '무료 시작' });
    await expect(registerLink).toBeVisible();
    await registerLink.click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('E2E-L04: should show navigation links', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('기능')).toBeVisible();
    await expect(page.getByText('요금제')).toBeVisible();
  });
});
