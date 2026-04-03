from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies import get_current_user, get_supabase_client
from app.schemas.subscription import SubscriptionResponse, PlanInfo, PlansListResponse, UpgradeRequest
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

PLANS = [
    PlanInfo(
        name="STARTER",
        display_name="Starter",
        price=0,
        currency="KRW",
        billing_period="monthly",
        features=["SD Matrix 기본 뷰", "Top Companies 기본 뷰", "주간 데이터 갱신"],
        is_popular=False,
    ),
    PlanInfo(
        name="PRO",
        display_name="Pro",
        price=49000,
        currency="KRW",
        billing_period="monthly",
        features=["전체 6개 분석 뷰", "드릴다운 분석", "트렌드 추적", "주간 리포트 이메일", "데이터 내보내기"],
        is_popular=True,
    ),
    PlanInfo(
        name="ENTERPRISE",
        display_name="Enterprise",
        price=149000,
        currency="KRW",
        billing_period="monthly",
        features=["Pro 전체 기능", "맞춤 리포트", "API 액세스", "전담 지원", "SLA 보장"],
        is_popular=False,
    ),
]

VALID_PLANS = {p.name for p in PLANS}


@router.get("/plans", response_model=ApiResponse[PlansListResponse])
async def get_plans():
    """요금제 목록 조회 (인증 불필요)"""
    return ApiResponse(data=PlansListResponse(plans=PLANS))


@router.get("/current", response_model=ApiResponse[SubscriptionResponse])
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """현재 사용자 구독 정보 조회"""
    from app.models.subscription import Subscription

    user_id = current_user["id"]
    # 활성 구독 조회 (최신순)
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if subscription:
        return ApiResponse(
            data=SubscriptionResponse(
                id=str(subscription.id),
                plan=subscription.plan,
                status=subscription.status,
                started_at=subscription.started_at,
                expires_at=subscription.expires_at,
            )
        )

    # 구독 레코드 없으면 현재 플랜으로 기본 응답 반환
    return ApiResponse(
        data=SubscriptionResponse(
            id="",
            plan=current_user.get("plan", "STARTER"),
            status="active",
            started_at=datetime.now(timezone.utc),
            expires_at=None,
        )
    )


@router.post("/upgrade", response_model=ApiResponse[SubscriptionResponse])
async def upgrade_plan(
    body: UpgradeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase=Depends(get_supabase_client),
):
    """구독 플랜 업그레이드

    - STARTER 전환: payment_key 불필요
    - PRO / ENTERPRISE 전환: payment_key 필수 (Toss 결제 완료 후 confirm 엔드포인트에서 처리 권장)
    """
    from app.models.subscription import Subscription
    import uuid

    plan = body.plan.upper()
    if plan not in VALID_PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"유효하지 않은 플랜입니다. 가능한 플랜: {', '.join(VALID_PLANS)}",
        )

    # 유료 플랜 전환 시 payment_key 필수
    if plan in ("PRO", "ENTERPRISE") and not body.payment_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유료 플랜 전환에는 payment_key가 필요합니다. /payments/confirm 엔드포인트를 먼저 호출하세요.",
        )

    user_id = current_user["id"]

    # 유료 플랜 전환 시 실제 결제 확인 — payment_key가 payments 테이블에 paid 상태로 존재해야 함
    if plan in ("PRO", "ENTERPRISE"):
        from app.models.payment import Payment
        verified = db.query(Payment).filter(
            Payment.payment_key == body.payment_key,
            Payment.user_id == user_id,
            Payment.status == "paid",
        ).first()
        if not verified:
            raise HTTPException(status_code=400, detail="유효한 결제 정보가 아닙니다.")

    now = datetime.now(timezone.utc)

    # 기존 활성 구독 취소
    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.status == "active",
    ).update({"status": "cancelled", "cancelled_at": now})

    # 새 구독 생성 (유료 플랜은 payment_key 저장)
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
    db.refresh(new_sub)

    # user_profiles.plan 업데이트
    supabase.table("user_profiles").update({"plan": plan}).eq("id", user_id).execute()

    return ApiResponse(
        data=SubscriptionResponse(
            id=str(new_sub.id),
            plan=new_sub.plan,
            status=new_sub.status,
            started_at=new_sub.started_at,
            expires_at=new_sub.expires_at,
        ),
        message=f"플랜이 {plan}으로 변경되었습니다.",
    )


@router.post("/cancel", response_model=ApiResponse[SubscriptionResponse])
async def cancel_subscription(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    supabase=Depends(get_supabase_client),
):
    """구독 취소"""
    from app.models.subscription import Subscription

    user_id = current_user["id"]
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활성 구독을 찾을 수 없습니다.",
        )

    now = datetime.now(timezone.utc)
    subscription.status = "cancelled"
    subscription.cancelled_at = now
    db.commit()
    db.refresh(subscription)

    # user_profiles.plan을 STARTER로 초기화
    supabase.table("user_profiles").update({"plan": "STARTER"}).eq("id", user_id).execute()

    return ApiResponse(
        data=SubscriptionResponse(
            id=str(subscription.id),
            plan=subscription.plan,
            status=subscription.status,
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
        ),
        message="구독이 취소되었습니다.",
    )
