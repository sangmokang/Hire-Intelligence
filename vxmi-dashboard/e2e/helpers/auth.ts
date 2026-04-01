import { Page } from '@playwright/test';

// 로그인 수행 — MSW가 /api/v1/auth/login을 처리
export async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.getByPlaceholder('이메일 주소').fill('admin@valueconnect.kr');
  await page.getByPlaceholder('비밀번호').fill('admin1234');
  await page.getByRole('button', { name: '이메일로 로그인' }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
}
