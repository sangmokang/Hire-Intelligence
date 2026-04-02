"""Toss Payments 결제 라우터"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import Field
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
    cancel_reason: str = Field(default="사용자 요청", max_length=200)


class CancelResponse(CamelModel):
    """결제 취소 응답"""
    payment_id: str
    status: str


async def _sync_user_plan(supabase, user_id: str, plan: str, context: str) -> None:
    """user_profiles.plan 동기화 (3회 재시도)"""
    for attempt in range(3):
        try:
            supabase.table("user_profiles").update({"plan": plan}).eq("id", user_id).execute()
            return
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                logger.warning("%s: user_profiles 동기화 실패 (3회 소진) user_id=%s: %s", context, user_id, e)


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

    # order_id로 결제 레코드 조회 (race condition 방지: FOR UPDATE 락)
    payment = (
        db.query(Payment)
        .filter(Payment.order_id == body.order_id, Payment.user_id == user_id)
        .with_for_update()
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

    # pending/paid 이외의 상태는 처리 불가 (failed, cancelled 등)
    if payment.status not in ("pending", "paid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"결제 확인이 불가능한 상태입니다: {payment.status}",
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
        # Toss API 오류 → 결제 실패 처리 (상세 에러는 로그, 응답은 generic)
        logger.error("Toss 결제 승인 실패 (order_id=%s): %s", body.order_id, exc)
        payment.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="결제 처리 중 오류가 발생했습니다.",
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

    # 보상 트랜잭션: DB 커밋 실패 시 Toss 결제 취소 시도
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.critical(
            "결제 승인 후 DB 커밋 실패 — 보상 취소 시도: user_id=%s, payment_key=%s",
            user_id, body.payment_key,
        )
        try:
            await payment_service.cancel_payment(body.payment_key, "DB 커밋 실패로 인한 자동 취소")
        except Exception:
            logger.critical("보상 취소도 실패 — 수동 개입 필요: payment_key=%s", body.payment_key)
        raise HTTPException(status_code=500, detail="결제 처리 중 오류가 발생했습니다.")

    # user_profiles.plan 업데이트 — 결제는 이미 완료됐으므로 실패해도 롤백 안 함
    await _sync_user_plan(supabase, str(user_id), plan, "confirm")

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
            # confirm 실패 시 웹훅으로 구독 보완 생성
            existing_sub = db.query(Subscription).filter(
                Subscription.user_id == payment.user_id,
                Subscription.payment_key == payment_key,
            ).first()
            if not existing_sub:
                # PLAN_AMOUNTS에서 플랜 역매핑
                amount_to_plan = {v: k for k, v in PLAN_AMOUNTS.items()}
                plan = amount_to_plan.get(payment.amount, "PRO")
                new_sub = Subscription(
                    id=uuid.uuid4(),
                    user_id=payment.user_id,
                    plan=plan,
                    status="active",
                    payment_key=payment_key,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                )
                db.add(new_sub)
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
        logger.error("Toss 결제 취소 실패 (payment_key=%s): %s", body.payment_key, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="결제 처리 중 오류가 발생했습니다.",
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
    await _sync_user_plan(supabase, str(user_id), "STARTER", "cancel")

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

    # 중복 결제 수단 등록 방지
    existing = db.query(BillingKey).filter(
        BillingKey.user_id == user_id,
        BillingKey.card_last_four == body.card_last_four,
        BillingKey.card_company == body.card_company,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 등록된 결제 수단입니다.")

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

    # key_id UUID 형식 검증
    try:
        key_uuid = uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 결제 수단 ID 형식입니다.")

    # IDOR 방지 — id + user_id 동시 조건
    key = (
        db.query(BillingKey)
        .filter(BillingKey.id == key_uuid, BillingKey.user_id == user_id)
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
