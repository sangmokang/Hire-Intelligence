"""Toss Payments 결제 라우터"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database import get_db
from app.dependencies import get_current_user, get_supabase_client
from app.models.billing_key import BillingKey, encrypt_billing_key, decrypt_billing_key
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.schemas.common import ApiResponse, CamelModel
from app.config import settings
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])

# 플랜별 결제 금액 (원화) — subscription.py PLANS와 일치
PLAN_AMOUNTS = {
    "PRO": 49000,
    "ENTERPRISE": 149000,
}


# ── 요청/응답 스키마 ──────────────────────────────────────────────

class PrepareRequest(CamelModel):
    """결제 준비 요청"""
    plan: str  # PRO / ENTERPRISE


class PrepareResponse(CamelModel):
    """결제 준비 응답 — 프론트에서 Toss 위젯 초기화에 사용"""
    order_id: str
    amount: int
    client_key: str


class ConfirmRequest(CamelModel):
    """결제 확인 요청 — Toss 결제 완료 후 프론트에서 전송"""
    payment_key: str
    order_id: str
    amount: int


class ConfirmResponse(CamelModel):
    """결제 확인 응답"""
    payment_id: str
    status: str
    plan: str


class CancelRequest(CamelModel):
    """결제 취소 요청"""
    payment_key: str
    cancel_reason: str = "사용자 요청"


class CancelResponse(CamelModel):
    """결제 취소 응답"""
    payment_id: str
    status: str


# ── 엔드포인트 ────────────────────────────────────────────────────

@router.post("/prepare", response_model=ApiResponse[PrepareResponse])
def prepare_payment(
    body: PrepareRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[PrepareResponse]:
    """결제 준비 — orderId 생성 후 DB에 pending 상태로 저장

    httpx 미사용, DB 저장만 수행하므로 동기(def) 사용.
    """
    plan = body.plan.upper()
    if plan not in PLAN_AMOUNTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"결제 가능한 플랜: {', '.join(PLAN_AMOUNTS.keys())}",
        )

    amount = PLAN_AMOUNTS[plan]
    order_id = f"HI-{uuid.uuid4().hex[:16].upper()}"
    user_id = current_user["id"]

    # pending 결제 레코드 생성
    payment = Payment(
        id=uuid.uuid4(),
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        status="pending",
    )
    db.add(payment)
    db.commit()

    return ApiResponse(
        data=PrepareResponse(
            order_id=order_id,
            amount=amount,
            client_key=settings.TOSS_CLIENT_KEY,
        )
    )


@router.post("/confirm", response_model=ApiResponse[ConfirmResponse])
async def confirm_payment(
    body: ConfirmRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase=Depends(get_supabase_client),
) -> ApiResponse[ConfirmResponse]:
    """결제 확인 — Toss API 호출 후 구독 활성화

    멱등성 보장: 이미 paid인 order_id는 재처리하지 않고 200 반환.
    """
    user_id = current_user["id"]

    # order_id로 pending 결제 레코드 조회
    payment = (
        db.query(Payment)
        .filter(Payment.order_id == body.order_id, Payment.user_id == user_id)
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결제 정보를 찾을 수 없습니다.",
        )

    # 멱등성: 이미 처리된 결제는 그대로 반환
    if payment.status == "paid":
        # 해당 결제와 연결된 활성 구독 플랜 조회
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.payment_key == payment.payment_key,
            )
            .first()
        )
        plan = subscription.plan if subscription else "PRO"
        return ApiResponse(
            data=ConfirmResponse(
                payment_id=str(payment.id),
                status="paid",
                plan=plan,
            )
        )

    # 금액 검증 — 변조 방지
    if payment.amount != body.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="결제 금액이 일치하지 않습니다.",
        )

    # Toss API 결제 승인 호출
    try:
        toss_result = await payment_service.confirm_payment(
            payment_key=body.payment_key,
            order_id=body.order_id,
            amount=body.amount,
        )
    except Exception as exc:
        # Toss API 오류 → 결제 실패 처리
        payment.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Toss 결제 승인 실패: {exc}",
        )

    now = datetime.now(timezone.utc)

    # 결제 레코드 갱신
    payment.payment_key = body.payment_key
    payment.status = "paid"
    payment.method = toss_result.get("method")
    payment.paid_at = now

    # 플랜 결정 — amount 기준 역산
    amount_to_plan = {v: k for k, v in PLAN_AMOUNTS.items()}
    plan = amount_to_plan.get(payment.amount, "PRO")

    # 기존 활성 구독 취소
    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
    ).update({"status": "cancelled", "cancelled_at": now})

    # 새 구독 활성화
    new_sub = Subscription(
        id=uuid.uuid4(),
        user_id=user_id,
        plan=plan,
        status="active",
        payment_key=body.payment_key,
        started_at=now,
    )
    db.add(new_sub)
    db.commit()

    # user_profiles.plan 업데이트 — 결제는 이미 완료됐으므로 실패해도 롤백 안 함
    # 3회 재시도 + 지수 백오프 (0.5s, 1s, 2s)
    for attempt in range(3):
        try:
            supabase.table("user_profiles").update({"plan": plan}).eq("id", str(user_id)).execute()
            break
        except Exception as exc:
            if attempt < 2:
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                # 3회 모두 실패 시 경고 로그만 남기고 진행 (결제는 유효)
                logger.warning(
                    "Supabase user_profiles 동기화 실패 (user_id=%s, plan=%s): %s",
                    user_id, plan, exc,
                )

    return ApiResponse(
        data=ConfirmResponse(
            payment_id=str(payment.id),
            status="paid",
            plan=plan,
        ),
        message=f"{plan} 플랜이 활성화되었습니다.",
    )


@router.post("/webhook")
async def toss_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Toss 웹훅 수신 — 인증 미들웨어 없음, HMAC-SHA256 시그니처 검증으로 보호

    이 엔드포인트는 Depends(get_current_user) 없이 동작하며,
    Toss가 전송하는 HMAC-SHA256 시그니처로 요청 무결성을 검증합니다.
    """
    raw_body = await request.body()
    signature = request.headers.get("TossPayments-Signature", "")

    # 시그니처 검증 실패 시 403
    if not payment_service.verify_webhook_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="웹훅 시그니처 검증 실패",
        )

    import json
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 웹훅 페이로드",
        )

    event_type = payload.get("eventType", "")
    data = payload.get("data", {})
    order_id = data.get("orderId")
    payment_key = data.get("paymentKey")
    toss_status = data.get("status")

    if not order_id:
        return {"received": True}

    # 결제 레코드 조회 후 상태 동기화
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if payment:
        now = datetime.now(timezone.utc)
        if toss_status == "DONE" and payment.status != "paid":
            payment.payment_key = payment_key
            payment.status = "paid"
            payment.paid_at = now
        elif toss_status == "CANCELED" and payment.status != "cancelled":
            payment.status = "cancelled"
            payment.cancelled_at = now
        elif toss_status == "ABORTED":
            payment.status = "failed"
        db.commit()

    return {"received": True}


@router.post("/cancel", response_model=ApiResponse[CancelResponse])
async def cancel_payment(
    body: CancelRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase=Depends(get_supabase_client),
) -> ApiResponse[CancelResponse]:
    """결제 취소 — Toss API 호출 후 구독 취소"""
    user_id = current_user["id"]

    # 결제 레코드 조회
    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_key == body.payment_key,
            Payment.user_id == user_id,
        )
        .first()
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결제 정보를 찾을 수 없습니다.",
        )

    if payment.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="취소 가능한 결제 상태가 아닙니다.",
        )

    # Toss API 결제 취소 호출
    try:
        await payment_service.cancel_payment(
            payment_key=body.payment_key,
            cancel_reason=body.cancel_reason,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Toss 결제 취소 실패: {exc}",
        )

    now = datetime.now(timezone.utc)

    # 결제 상태 취소 처리
    payment.status = "cancelled"
    payment.cancelled_at = now

    # 연결된 활성 구독 취소
    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.payment_key == body.payment_key,
        Subscription.status == "active",
    ).update({"status": "cancelled", "cancelled_at": now})

    db.commit()

    # user_profiles.plan을 STARTER로 초기화 (재시도 포함)
    for attempt in range(3):
        try:
            supabase.table("user_profiles").update({"plan": "STARTER"}).eq("id", str(user_id)).execute()
            break
        except Exception as e:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                logger.warning("cancel: user_profiles 동기화 실패 (3회 재시도 소진) user_id=%s: %s", user_id, e)

    return ApiResponse(
        data=CancelResponse(
            payment_id=str(payment.id),
            status="cancelled",
        ),
        message="결제가 취소되었습니다.",
    )


# ── 결제 수단(빌링키) 스키마 ──────────────────────────────────────

class BillingKeyRegisterRequest(CamelModel):
    """빌링키 등록 요청"""
    customer_key: str
    billing_key: str
    card_last_four: str
    card_company: str


class BillingKeyResponse(CamelModel):
    """빌링키 응답"""
    id: str
    customer_key: str
    card_last_four: str
    card_company: str
    is_default: bool
    created_at: str


# ── 결제 수단(빌링키) 엔드포인트 ─────────────────────────────────

@router.get("/methods", response_model=ApiResponse[list[BillingKeyResponse]])
def list_payment_methods(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[list[BillingKeyResponse]]:
    """현재 사용자의 등록된 결제 수단 목록 조회"""
    user_id = current_user["id"]
    keys = (
        db.query(BillingKey)
        .filter(BillingKey.user_id == user_id)
        .order_by(BillingKey.created_at.desc())
        .all()
    )
    return ApiResponse(
        data=[
            BillingKeyResponse(
                id=str(k.id),
                customer_key=k.customer_key,
                card_last_four=k.card_last_four,
                card_company=k.card_company,
                is_default=k.is_default,
                created_at=k.created_at.isoformat(),
            )
            for k in keys
        ]
    )


@router.post("/methods", response_model=ApiResponse[BillingKeyResponse])
async def register_payment_method(
    body: BillingKeyRegisterRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BillingKeyResponse]:
    """새 결제 수단(빌링키) 등록

    첫 번째 카드 등록 시 자동으로 기본 결제 수단으로 설정된다.
    """
    user_id = current_user["id"]

    # Toss 빌링키 유효성 검증 (mock 모드에서는 항상 성공)
    try:
        await payment_service.issue_billing_key(
            customer_key=body.customer_key,
            auth_key=body.billing_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"빌링키 발급 실패: {exc}",
        )

    # 첫 번째 카드 여부 확인 — 기본 결제 수단 자동 설정
    existing_count = (
        db.query(BillingKey)
        .filter(BillingKey.user_id == user_id)
        .count()
    )
    is_default = existing_count == 0

    new_key = BillingKey(
        id=uuid.uuid4(),
        user_id=user_id,
        customer_key=body.customer_key,
        billing_key=encrypt_billing_key(body.billing_key),
        card_last_four=body.card_last_four,
        card_company=body.card_company,
        is_default=is_default,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return ApiResponse(
        data=BillingKeyResponse(
            id=str(new_key.id),
            customer_key=new_key.customer_key,
            card_last_four=new_key.card_last_four,
            card_company=new_key.card_company,
            is_default=new_key.is_default,
            created_at=new_key.created_at.isoformat(),
        ),
        message="결제 수단이 등록되었습니다.",
    )


@router.delete("/methods/{key_id}", response_model=ApiResponse[None])
def delete_payment_method(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    """결제 수단 삭제

    IDOR 방지: user_id 조건을 함께 적용하여 타인의 카드 삭제 불가.
    기본 카드 삭제 시 가장 오래된 남은 카드를 기본으로 승격한다.
    """
    user_id = current_user["id"]

    # IDOR 방지 — id + user_id 동시 조건
    key = (
        db.query(BillingKey)
        .filter(BillingKey.id == key_id, BillingKey.user_id == user_id)
        .first()
    )
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결제 수단을 찾을 수 없습니다.",
        )

    was_default = key.is_default
    db.delete(key)
    db.flush()

    # 기본 카드 삭제 시 가장 오래된 남은 카드를 기본으로 승격
    if was_default:
        oldest_remaining = (
            db.query(BillingKey)
            .filter(BillingKey.user_id == user_id)
            .order_by(BillingKey.created_at.asc())
            .first()
        )
        if oldest_remaining:
            oldest_remaining.is_default = True

    db.commit()

    return ApiResponse(data=None, message="결제 수단이 삭제되었습니다.")
