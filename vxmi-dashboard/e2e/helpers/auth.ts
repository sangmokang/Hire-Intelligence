import { Page } from '@playwright/test';

// Supabase auth 응답 mock — signInWithPassword 인터셉트
export async function mockSupabaseAuth(page: Page) {
  // Supabase token endpoint mock
  await page.route('**/auth/v1/token**', async (route) => {
    const request = route.request();
    if (request.method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-access-token-for-e2e',
          token_type: 'bearer',
          expires_in: 3600,
          expires_at: Math.floor(Date.now() / 1000) + 3600,
          refresh_token: 'mock-refresh-token',
          user: {
            id: 'sa-001',
            aud: 'authenticated',
            role: 'authenticated',
            email: 'admin@valueconnect.kr',
            email_confirmed_at: '2024-01-15T09:00:00Z',
            app_metadata: { provider: 'email' },
            user_metadata: { name: '김관리' },
            created_at: '2024-01-15T09:00:00Z',
          },
        }),
      });
    } else {
      await route.continue();
    }
  });

  // Supabase getUser endpoint mock
  await page.route('**/auth/v1/user**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'sa-001',
        aud: 'authenticated',
        role: 'authenticated',
        email: 'admin@valueconnect.kr',
        email_confirmed_at: '2024-01-15T09:00:00Z',
        app_metadata: { provider: 'email' },
        user_metadata: { name: '김관리' },
        created_at: '2024-01-15T09:00:00Z',
      }),
    });
  });

  // Supabase getSession mock
  await page.route('**/auth/v1/session**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-access-token-for-e2e',
        token_type: 'bearer',
        expires_in: 3600,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
        refresh_token: 'mock-refresh-token',
        user: {
          id: 'sa-001',
          aud: 'authenticated',
          role: 'authenticated',
          email: 'admin@valueconnect.kr',
          email_confirmed_at: '2024-01-15T09:00:00Z',
          app_metadata: { provider: 'email' },
          user_metadata: { name: '김관리' },
          created_at: '2024-01-15T09:00:00Z',
        },
      }),
    });
  });
}

// 로그인 수행 (Supabase mock + 폼 제출)
export async function loginAsAdmin(page: Page) {
  await mockSupabaseAuth(page);
  await page.goto('/login');
  await page.getByPlaceholder('이메일 주소').fill('admin@valueconnect.kr');
  await page.getByPlaceholder('비밀번호').fill('admin1234');
  await page.getByRole('button', { name: '이메일로 로그인' }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 15000 });
}
