import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('E2E-001: should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/');
    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
    // Should show login form
    await expect(page.getByPlaceholder('이메일 주소')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호')).toBeVisible();
    await expect(page.getByText('Google로 계속하기')).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login');
    await page.getByText('이메일로 로그인').click();
    // Should show validation errors
    await expect(page.getByText('유효한 이메일')).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');
    await page.getByText('회원가입').click();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByText('회원가입')).toBeVisible();
  });

  test('should navigate to forgot password page', async ({ page }) => {
    await page.goto('/login');
    await page.getByText('비밀번호 찾기').click();
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test('E2E-A01: should show error message on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('이메일 주소').fill('wrong@example.com');
    await page.getByPlaceholder('비밀번호').fill('wrongpassword');
    await page.getByText('이메일로 로그인').click();
    // MSW returns 401 with Korean error message
    await expect(page.getByText('이메일 또는 비밀번호가 올바르지 않습니다.')).toBeVisible();
  });

  test('E2E-A02: should show register page with required fields', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByPlaceholder('이름')).toBeVisible();
    await expect(page.getByPlaceholder('이메일 주소')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호 (8자 이상, 대문자·숫자 포함)')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호 확인')).toBeVisible();
  });
});
