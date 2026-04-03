import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('E2E-001: should show login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByPlaceholder('이메일 주소')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호')).toBeVisible();
    await expect(page.getByText('Google로 계속하기')).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/login');
    await page.getByRole('button', { name: '이메일로 로그인' }).click();
    // loginSchema: email — '유효한 이메일 주소를 입력해주세요.'
    await expect(page.getByText('유효한 이메일')).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login');
    // 'Register' 링크는 <Link to="/register"> 텍스트 '회원가입'
    await page.getByRole('link', { name: '회원가입' }).click();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: '회원가입' })).toBeVisible();
  });

  test('should navigate to forgot password page', async ({ page }) => {
    await page.goto('/login');
    await page.getByText('비밀번호 찾기').click();
    await expect(page).toHaveURL(/\/forgot-password/);
  });

  test('E2E-A01: should show error on invalid credentials', async ({ page }) => {
    // MSW가 /api/v1/auth/login을 가로채서 잘못된 자격증명에 대해 401 반환
    await page.goto('/login');
    await page.getByPlaceholder('이메일 주소').fill('wrong@example.com');
    await page.getByPlaceholder('비밀번호').fill('Wrongpass1');
    await page.getByRole('button', { name: '이메일로 로그인' }).click();
    await expect(page.getByText(/올바르지 않|실패|오류/i)).toBeVisible({ timeout: 5000 });
  });

  test('E2E-A02: should show register page with required fields', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByPlaceholder('이름')).toBeVisible();
    await expect(page.getByPlaceholder('이메일 주소')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호 (8자 이상, 대문자·숫자 포함)')).toBeVisible();
    await expect(page.getByPlaceholder('비밀번호 확인')).toBeVisible();
  });

  test('E2E-A03: should complete register flow and enter dashboard', async ({ page }) => {
    const email = `qa-${Date.now()}@example.com`;

    await page.goto('/register');
    await page.getByPlaceholder('이름').fill('QA User');
    await page.getByPlaceholder('이메일 주소').fill(email);
    await page.getByPlaceholder('비밀번호 (8자 이상, 대문자·숫자 포함)').fill('Password1');
    await page.getByPlaceholder('비밀번호 확인').fill('Password1');
    await page.getByRole('button', { name: '회원가입' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Unexpected Application Error!')).not.toBeVisible();
  });

  test('E2E-A04: should keep auth state after dashboard reload', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('이메일 주소').fill('admin@valueconnect.kr');
    await page.getByPlaceholder('비밀번호').fill('admin1234');
    await page.getByRole('button', { name: '이메일로 로그인' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await page.goto('/dashboard/top-companies');
    await page.reload();

    await expect(page).toHaveURL(/\/dashboard\/top-companies/);
    await expect(page.getByText('로그인')).not.toBeVisible();
    await expect(page.getByText('Unexpected Application Error!')).not.toBeVisible();
  });
});
