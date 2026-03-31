import { test, expect } from '@playwright/test';

test.describe('Landing Page', () => {
  test('E2E-L01: should display landing page at root URL', async ({ page }) => {
    await page.goto('/');
    // nav에 ValueHire span 텍스트 (exact match로 첫 번째 요소)
    await expect(page.getByText('ValueHire').first()).toBeVisible();
  });

  test('E2E-L02: should have login link', async ({ page }) => {
    await page.goto('/');
    // nav의 <Link to="/login"> 텍스트 '로그인'
    const loginLink = page.getByRole('link', { name: '로그인' });
    await expect(loginLink).toBeVisible();
    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('E2E-L03: should have register CTA', async ({ page }) => {
    await page.goto('/');
    // nav의 <Link to="/register"> 텍스트 '무료 시작' (exact)
    const registerLink = page.getByRole('link', { name: '무료 시작', exact: true });
    await expect(registerLink).toBeVisible();
    await registerLink.click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('E2E-L04: should show navigation links', async ({ page }) => {
    await page.goto('/');
    // nav의 <a href="#features">기능</a> — a 태그지만 role=link
    await expect(page.locator('a[href="#features"]').first()).toBeVisible();
    await expect(page.locator('a[href="#pricing"]').first()).toBeVisible();
  });
});
