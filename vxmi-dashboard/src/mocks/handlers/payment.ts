import { http, HttpResponse, delay } from 'msw';

interface PreparePaymentRequest {
  plan: string;
}

interface ConfirmPaymentRequest {
  paymentKey: string;
  orderId: string;
  amount: number;
}

interface CancelPaymentRequest {
  orderId: string;
  cancelReason?: string;
}

let orderCounter = 1000;

export const paymentHandlers = [
  // 결제 준비 — orderId와 amount 반환
  http.post('/api/v1/payments/prepare', async ({ request }) => {
    await delay(300);
    const body = await request.json() as PreparePaymentRequest;

    const priceMap: Record<string, number> = {
      PRO: 49000,
      ENTERPRISE: 149000,
    };

    const amount = priceMap[body.plan] ?? 0;
    const orderId = `order-${Date.now()}-${orderCounter++}`;
    const orderName = body.plan === 'PRO' ? 'Hire Intelligence Pro 월 구독' : 'Hire Intelligence Enterprise 월 구독';

    return HttpResponse.json({
      status: 'success',
      data: { orderId, amount, orderName },
      message: null,
    });
  }),

  // 결제 확인 — Toss 콜백 후 서버 검증
  http.post('/api/v1/payments/confirm', async ({ request }) => {
    await delay(400);
    const body = await request.json() as ConfirmPaymentRequest;

    // 목 환경에서는 항상 성공 처리
    return HttpResponse.json({
      status: 'success',
      data: {
        paymentKey: body.paymentKey,
        orderId: body.orderId,
        amount: body.amount,
        status: 'DONE',
        approvedAt: new Date().toISOString(),
      },
      message: '결제가 완료되었습니다.',
    });
  }),

  // 결제 취소
  http.post('/api/v1/payments/cancel', async ({ request }) => {
    await delay(300);
    const body = await request.json() as CancelPaymentRequest;

    return HttpResponse.json({
      status: 'success',
      data: {
        orderId: body.orderId,
        status: 'CANCELED',
        canceledAt: new Date().toISOString(),
      },
      message: '결제가 취소되었습니다.',
    });
  }),
];
