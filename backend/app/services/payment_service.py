"""Toss Payments 연동 서비스"""
import base64
import hashlib
import hmac

import httpx

from app.config import settings


class TossPaymentService:
    """Toss Payments API 클라이언트"""

    BASE_URL = "https://api.tosspayments.com/v1"

    def __init__(self) -> None:
        self.secret_key = settings.TOSS_SECRET_KEY
        # TOSS_SECRET_KEY 미설정 시 목(mock) 모드로 동작
        self._enabled = bool(self.secret_key)

    def _auth_header(self) -> str:
        """Basic 인증 헤더 값 반환 (secret_key + ':' base64 인코딩)"""
        encoded = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        return f"Basic {encoded}"

    async def confirm_payment(
        self, payment_key: str, order_id: str, amount: int
    ) -> dict:
        """Toss confirmPayment API 호출 — 결제 승인"""
        if not self._enabled:
            # 개발/테스트 환경: 실제 API 미호출
            return {
                "status": "DONE",
                "paymentKey": payment_key,
                "orderId": order_id,
                "totalAmount": amount,
                "method": "카드",
                "approvedAt": None,
                "_mock": True,
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments/confirm",
                json={
                    "paymentKey": payment_key,
                    "orderId": order_id,
                    "amount": amount,
                },
                headers={
                    "Authorization": self._auth_header(),
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def cancel_payment(self, payment_key: str, cancel_reason: str) -> dict:
        """Toss cancelPayment API 호출 — 결제 취소"""
        if not self._enabled:
            return {"status": "CANCELED", "paymentKey": payment_key, "_mock": True}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments/{payment_key}/cancel",
                json={"cancelReason": cancel_reason},
                headers={
                    "Authorization": self._auth_header(),
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """HMAC-SHA256 웹훅 시그니처 검증

        Toss는 요청 바디를 HMAC-SHA256(TOSS_WEBHOOK_SECRET)으로 서명 후
        'TossPayments-Signature' 헤더로 전송한다.
        """
        if not settings.TOSS_WEBHOOK_SECRET:
            # 웹훅 시크릿 미설정 시 검증 통과 (개발 환경 편의)
            return True

        expected = hmac.new(
            settings.TOSS_WEBHOOK_SECRET.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# 싱글톤 인스턴스
payment_service = TossPaymentService()
