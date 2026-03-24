import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('유효한 이메일 주소를 입력해주세요.'),
  password: z.string().min(8, '비밀번호는 8자 이상이어야 합니다.'),
  rememberMe: z.boolean().optional(),
});

export const registerSchema = z
  .object({
    email: z.string().email('유효한 이메일 주소를 입력해주세요.'),
    password: z
      .string()
      .min(8, '비밀번호는 8자 이상이어야 합니다.')
      .regex(/[A-Z]/, '대문자를 포함해야 합니다.')
      .regex(/[0-9]/, '숫자를 포함해야 합니다.'),
    confirmPassword: z.string(),
    name: z.string().min(2, '이름은 2자 이상이어야 합니다.'),
    category: z.enum(['JOB_SEEKER', 'INHOUSE_HR', 'HEADHUNTER', 'CHRO']),
    company: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '비밀번호가 일치하지 않습니다.',
    path: ['confirmPassword'],
  });

export const forgotPasswordSchema = z.object({
  email: z.string().email('유효한 이메일 주소를 입력해주세요.'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
