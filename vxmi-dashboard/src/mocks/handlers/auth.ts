import { http, HttpResponse, delay } from 'msw';
import { mockUsers, testAccounts } from '../data/users';

// Simple mock JWT (not real - just for dev)
function createMockJWT(user: typeof mockUsers[0]): string {
  const payload = {
    sub: user.id,
    email: user.email,
    role: user.role,
    category: user.category,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 900, // 15 min
  };
  // Base64 encode (not cryptographically valid, just for mock)
  return `mock.${btoa(JSON.stringify(payload))}.signature`;
}

// NOTE: currentUser is in-memory only and resets on page reload (Vite HMR).
// The "restore session from cookie" flow cannot be tested via MSW.
// Users must log in again after a hard reload in dev mode.
let currentUser: typeof mockUsers[0] | null = null;

export const authHandlers = [
  // Login
  http.post('/api/v1/auth/login', async ({ request }) => {
    await delay(300);
    const body = await request.json() as { email: string; password: string };

    // Find matching test account
    const account = Object.values(testAccounts).find(a => a.email === body.email);
    if (!account || account.password !== body.password) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_INVALID_CREDENTIALS', message: '이메일 또는 비밀번호가 올바르지 않습니다.' } },
        { status: 401 }
      );
    }

    const user = mockUsers.find(u => u.email === body.email)!;
    currentUser = user;

    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken: createMockJWT(user),
        user,
      },
    });
  }),

  // Register
  http.post('/api/v1/auth/register', async ({ request }) => {
    await delay(500);
    const body = await request.json() as { email: string; password: string; name: string; category: string; company?: string };

    // Check duplicate email
    if (mockUsers.some(u => u.email === body.email)) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_DUPLICATE_EMAIL', message: '이미 등록된 이메일입니다.' } },
        { status: 409 }
      );
    }

    // 카테고리에 따른 트랙 및 기본 플랜 결정
    const isJobSeeker = body.category === 'JOB_SEEKER';
    const newUser = {
      id: `u-${Date.now()}`,
      email: body.email,
      name: body.name,
      role: 'USER' as const,
      category: body.category as import('../../types/auth').UserCategory,
      plan: (isJobSeeker ? 'TALENT_FREE' : 'STARTER') as import('../../types/auth').PlanType,
      track: (isJobSeeker ? 'TALENT' : 'BUSINESS') as 'TALENT' | 'BUSINESS',
      status: 'ACTIVE' as const,
      company: body.company,
      authProvider: 'EMAIL' as const,
      createdAt: new Date().toISOString(),
    };

    currentUser = newUser as any;

    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken: createMockJWT(newUser as any),
        user: newUser,
      },
    }, { status: 201 });
  }),

  // Refresh token (silent refresh)
  http.post('/api/v1/auth/refresh', async () => {
    await delay(100);
    if (!currentUser) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_TOKEN_EXPIRED', message: 'Refresh token expired' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken: createMockJWT(currentUser),
        user: currentUser,
      },
    });
  }),

  // Logout
  http.post('/api/v1/auth/logout', async () => {
    await delay(100);
    currentUser = null;
    return HttpResponse.json({ status: 'success' });
  }),

  // Get current user
  http.get('/api/v1/auth/me', async () => {
    await delay(100);
    if (!currentUser) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_UNAUTHORIZED', message: 'Not authenticated' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      status: 'success',
      data: { user: currentUser },
    });
  }),
];
