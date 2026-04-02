"""Toss Payments 결제 서비스 + 라우터 테스트 (15개)"""
import base64
import hashlib
import hmac
import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.payment import Payment
from app.models.subscription import Subscription

client = TestClient(app)


# ── 헬퍼 ──────────────────────────────────────────────────────────

def _make_payment(
    order_id: str = "HI-TESTORDER0001",
    user_id: str = "test-uuid",
    amount: int = 49000,
    status: str = "pending",
    payment_key: str | None = None,
) -> MagicMock:
    """테스트용 Payment MagicMock 생성"""
    p = MagicMock(spec=Payment)
    p.id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    p.order_id = order_id
    p.user_id = user_id
    p.amount = amount
    p.status = status
    p.payment_key = payment_key
    return p


def _make_subscription(plan: str = "PRO", payment_key: str = "toss-key-1") -> MagicMock:
    """테스트용 Subscription MagicMock 생성"""
    s = MagicMock(spec=Subscription)
    s.plan = plan
    s.payment_key = payment_key
    s.status = "active"
    return s


# ── Unit 테스트: TossPaymentService ───────────────────────────────

class TestTossPaymentServiceUnit:
    """TOSS_SECRET_KEY 미설정(목 모드) + 웹훅 시그니처 검증 단위 테스트"""

    def test_confirm_payment_mock_mode(self):
        """TOSS_SECRET_KEY 미설정 → _mock: True 포함된 mock 응답 반환"""
        from app.services.payment_service import TossPaymentService
        import asyncio

        svc = TossPaymentService.__new__(TossPaymentService)
        svc.secret_key = None
        svc._enabled = False

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            svc.confirm_payment("key123", "order123", 49000)
        )
        loop.close()
        assert result["status"] == "DONE"
        assert result["_mock"] is True
        assert result["paymentKey"] == "key123"
        assert result["orderId"] == "order123"
        assert result["totalAmount"] == 49000

    def test_cancel_payment_mock_mode(self):
        """TOSS_SECRET_KEY 미설정 → 취소도 mock 응답 반환"""
        from app.services.payment_service import TossPaymentService
        import asyncio

        svc = TossPaymentService.__new__(TossPaymentService)
        svc.secret_key = None
        svc._enabled = False

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            svc.cancel_payment("key-cancel", "환불 요청")
        )
        loop.close()
        assert result["status"] == "CANCELED"
        assert result["_mock"] is True
        assert result["paymentKey"] == "key-cancel"

    def test_verify_webhook_signature_no_secret(self):
        """TOSS_WEBHOOK_SECRET 미설정 시 항상 True 반환 (개발 편의)"""
        from app.services.payment_service import TossPaymentService
        from app.config import settings

        svc = TossPaymentService.__new__(TossPaymentService)
        svc.secret_key = None
        svc._enabled = False

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", None):
            result = svc.verify_webhook_signature(b"any-body", "any-signature")
        assert result is True

    def test_verify_webhook_signature_valid(self):
        """올바른 Base64 HMAC-SHA256 시그니처 → True"""
        from app.services.payment_service import TossPaymentService
        from app.config import settings

        raw_body = b'{"eventType":"PAYMENT_STATUS_CHANGED"}'
        secret = "test-webhook-secret"

        # 정상 시그니처 생성 (Base64 HMAC-SHA256)
        digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
        valid_sig = base64.b64encode(digest).decode()

        svc = TossPaymentService.__new__(TossPaymentService)
        svc.secret_key = None
        svc._enabled = False

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", secret):
            result = svc.verify_webhook_signature(raw_body, valid_sig)
        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """잘못된 시그니처 → False"""
        from app.services.payment_service import TossPaymentService
        from app.config import settings

        raw_body = b'{"eventType":"PAYMENT_STATUS_CHANGED"}'
        secret = "test-webhook-secret"

        svc = TossPaymentService.__new__(TossPaymentService)
        svc.secret_key = None
        svc._enabled = False

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", secret):
            result = svc.verify_webhook_signature(raw_body, "invalid-signature==")
        assert result is False


# ── Integration 테스트: 라우터 ────────────────────────────────────

class TestPreparePayment:
    """결제 준비 엔드포인트 테스트"""

    def test_prepare_payment_success(self, mock_user, mock_db, mock_supabase):
        """유효한 PRO 플랜 → 200, orderId 반환"""
        response = client.post(
            "/api/v1/payments/prepare",
            json={"plan": "PRO"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "orderId" in data["data"]
        assert data["data"]["orderId"].startswith("HI-")
        assert data["data"]["amount"] == 49000

    def test_prepare_payment_invalid_plan(self, mock_user, mock_db, mock_supabase):
        """존재하지 않는 플랜 → 400"""
        response = client.post(
            "/api/v1/payments/prepare",
            json={"plan": "INVALID"},
        )
        assert response.status_code == 400


class TestConfirmPayment:
    """결제 확인 엔드포인트 테스트"""

    def test_confirm_payment_success(self, mock_user, mock_db, mock_supabase):
        """준비→확인 플로우 (목 모드) → 200, paid 반환"""
        # pending 결제 레코드 mock (with_for_update() 체인 포함)
        pending = _make_payment(amount=49000, status="pending")
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = pending

        # 구독 update chain mock
        mock_db.query.return_value.filter.return_value.update.return_value = 1

        response = client.post(
            "/api/v1/payments/confirm",
            json={
                "paymentKey": "toss-pk-success",
                "orderId": "HI-TESTORDER0001",
                "amount": 49000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "paid"
        assert data["data"]["plan"] == "PRO"

    def test_confirm_payment_idempotent(self, mock_user, mock_db, mock_supabase):
        """이미 paid인 order_id 재확인 → 200 (멱등성 보장)"""
        paid = _make_payment(amount=49000, status="paid", payment_key="toss-pk-existing")

        # 첫 번째 query (payment), 두 번째 query (subscription)
        sub = _make_subscription(plan="PRO", payment_key="toss-pk-existing")

        def side_effect_query(model):
            m = MagicMock()
            if model.__name__ == "Payment":
                # with_for_update() 체인 지원
                m.filter.return_value.with_for_update.return_value.first.return_value = paid
            else:
                m.filter.return_value.first.return_value = sub
            return m

        mock_db.query.side_effect = side_effect_query

        response = client.post(
            "/api/v1/payments/confirm",
            json={
                "paymentKey": "toss-pk-existing",
                "orderId": "HI-TESTORDER0001",
                "amount": 49000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "paid"

    def test_confirm_payment_amount_mismatch(self, mock_user, mock_db, mock_supabase):
        """결제 금액 불일치 → 400"""
        pending = _make_payment(amount=49000, status="pending")
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = pending

        response = client.post(
            "/api/v1/payments/confirm",
            json={
                "paymentKey": "toss-pk-mismatch",
                "orderId": "HI-TESTORDER0001",
                "amount": 99999,  # 잘못된 금액
            },
        )
        assert response.status_code == 400


class TestCancelPayment:
    """결제 취소 엔드포인트 테스트"""

    def test_cancel_payment_success(self, mock_user, mock_db, mock_supabase):
        """paid 결제 취소 → 200, cancelled 반환 + 구독 취소"""
        paid = _make_payment(amount=49000, status="paid", payment_key="toss-pk-cancel")
        mock_db.query.return_value.filter.return_value.first.return_value = paid
        mock_db.query.return_value.filter.return_value.update.return_value = 1

        response = client.post(
            "/api/v1/payments/cancel",
            json={
                "paymentKey": "toss-pk-cancel",
                "cancelReason": "테스트 취소",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "cancelled"

    def test_cancel_payment_not_found(self, mock_user, mock_db, mock_supabase):
        """존재하지 않는 payment_key → 404"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post(
            "/api/v1/payments/cancel",
            json={
                "paymentKey": "nonexistent-key",
                "cancelReason": "없는 결제",
            },
        )
        assert response.status_code == 404


class TestWebhook:
    """Toss 웹훅 엔드포인트 테스트"""

    def _make_webhook_body(self, event_type: str, order_id: str, toss_status: str) -> bytes:
        """웹훅 페이로드 생성"""
        payload = {
            "eventType": event_type,
            "data": {
                "orderId": order_id,
                "paymentKey": "toss-wh-key",
                "status": toss_status,
            },
        }
        return json.dumps(payload).encode()

    def test_webhook_invalid_signature(self, mock_db):
        """잘못된 시그니처 → 403"""
        from app.config import settings

        raw_body = self._make_webhook_body("PAYMENT_STATUS_CHANGED", "HI-WH001", "DONE")

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", "real-secret"):
            response = client.post(
                "/api/v1/payments/webhook",
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "TossPayments-Signature": "invalid-bad-signature==",
                },
            )
        assert response.status_code == 403

    def test_webhook_valid_done(self, mock_db):
        """DONE 이벤트 + 올바른 시그니처 → 200, payment.status = paid"""
        from app.config import settings

        secret = "test-wh-secret"
        raw_body = self._make_webhook_body("PAYMENT_STATUS_CHANGED", "HI-WH002", "DONE")

        digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
        valid_sig = base64.b64encode(digest).decode()

        # pending 결제 mock
        pending = _make_payment(order_id="HI-WH002", status="pending")
        mock_db.query.return_value.filter.return_value.first.return_value = pending

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", secret):
            response = client.post(
                "/api/v1/payments/webhook",
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "TossPayments-Signature": valid_sig,
                },
            )
        assert response.status_code == 200
        # pending → paid 상태 전환 확인
        assert pending.status == "paid"

    def test_webhook_valid_canceled(self, mock_db):
        """CANCELED 이벤트 + 올바른 시그니처 → 200, payment.status = cancelled"""
        from app.config import settings

        secret = "test-wh-secret"
        raw_body = self._make_webhook_body("PAYMENT_STATUS_CHANGED", "HI-WH003", "CANCELED")

        digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
        valid_sig = base64.b64encode(digest).decode()

        # paid 결제 mock
        paid = _make_payment(order_id="HI-WH003", status="paid")
        mock_db.query.return_value.filter.return_value.first.return_value = paid

        with patch.object(settings, "TOSS_WEBHOOK_SECRET", secret):
            response = client.post(
                "/api/v1/payments/webhook",
                content=raw_body,
                headers={
                    "Content-Type": "application/json",
                    "TossPayments-Signature": valid_sig,
                },
            )
        assert response.status_code == 200
        # paid → cancelled 상태 전환 확인
        assert paid.status == "cancelled"
