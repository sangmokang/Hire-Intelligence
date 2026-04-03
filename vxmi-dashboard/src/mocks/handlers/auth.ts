import { http, HttpResponse, delay } from 'msw';
import { mockUsers, testAccounts } from '../data/users';
import type { User } from '../../types/auth';

function encodeBase64Json(value: unknown): string {
  const json = JSON.stringify(value);
  const bytes = new TextEncoder().encode(json);
  let binary = '';

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}

function decodeBase64Json<T>(value: string): T {
  const binary = atob(value);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  const json = new TextDecoder().decode(bytes);
  return JSON.parse(json) as T;
}

// Simple mock JWT (not real - just for dev)
function createMockJWT(user: User): string {
  const payload = {
    sub: user.id,
    email: user.email,
    name: user.name,
    role: user.role,
    category: user.category,
    plan: user.plan,
    track: user.track,
    status: user.status,
    company: user.company,
    authProvider: user.authProvider,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 900, // 15 min
  };
  // Base64 encode (not cryptographically valid, just for mock)
  return `mock.${encodeBase64Json(payload)}.signature`;
}

function decodeMockJWT(token?: string | null): User | null {
  if (!token) return null;

  const [, encodedPayload] = token.split('.');
  if (!encodedPayload) return null;

  try {
    const payload = decodeBase64Json<Partial<User> & { email?: string }>(encodedPayload);
    const user = findUserByEmail(payload.email);
    if (user) return user;

    if (!payload.email || !payload.id || !payload.name || !payload.role || !payload.category || !payload.plan || !payload.track || !payload.status || !payload.authProvider) {
      return null;
    }

    return {
      id: payload.id,
      email: payload.email,
      name: payload.name,
      role: payload.role,
      category: payload.category,
      plan: payload.plan,
      track: payload.track,
      status: payload.status,
      company: payload.company,
      authProvider: payload.authProvider,
    } satisfies User;
  } catch {
    return null;
  }
}

function extractBearerToken(authHeader: string | null): string | null {
  if (!authHeader?.startsWith('Bearer ')) return null;
  return authHeader.slice('Bearer '.length);
}

const runtimeUsers = new Map<string, User>();

function findUserByEmail(email?: string | null): User | null {
  if (!email) return null;
  return runtimeUsers.get(email) ?? mockUsers.find((user) => user.email === email) ?? null;
}

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
    const accessToken = createMockJWT(user);
    const refreshToken = createMockJWT(user);

    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken,
        refreshToken,
        user,
      },
    });
  }),

  // Register
  http.post('/api/v1/auth/signup', async ({ request }) => {
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
    const newUser: User = {
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

    runtimeUsers.set(newUser.email, newUser);
    const accessToken = createMockJWT(newUser);
    const refreshToken = createMockJWT(newUser);

    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken,
        refreshToken,
        user: newUser,
      },
    }, { status: 201 });
  }),

  // Refresh token (silent refresh)
  http.post('/api/v1/auth/refresh', async ({ request }) => {
    await delay(100);
    const body = await request.json().catch(() => ({})) as { refreshToken?: string };
    const user = decodeMockJWT(body.refreshToken);

    if (!user) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_TOKEN_EXPIRED', message: 'Refresh token expired' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      status: 'success',
      data: {
        accessToken: createMockJWT(user),
        refreshToken: createMockJWT(user),
        user,
      },
    });
  }),

  // Logout
  http.post('/api/v1/auth/logout', async () => {
    await delay(100);
    return HttpResponse.json({ status: 'success' });
  }),

  // Get current user
  http.get('/api/v1/auth/me', async ({ request }) => {
    await delay(100);
    const token = extractBearerToken(request.headers.get('authorization'));
    const user = decodeMockJWT(token);

    if (!user) {
      return HttpResponse.json(
        { status: 'error', error: { code: 'AUTH_UNAUTHORIZED', message: 'Not authenticated' } },
        { status: 401 }
      );
    }
    return HttpResponse.json({
      status: 'success',
      data: { user },
    });
  }),
];
