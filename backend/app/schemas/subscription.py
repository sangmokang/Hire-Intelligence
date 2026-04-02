from datetime import datetime
from typing import Optional
from app.schemas.common import CamelModel


class UpgradeRequest(CamelModel):
    """구독 업그레이드 요청 — PRO/ENTERPRISE는 payment_key 필수"""
    plan: str
    payment_key: str | None = None


class SubscriptionResponse(CamelModel):
    """현재 구독 정보 응답"""
    id: str
    plan: str
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None


class PlanInfo(CamelModel):
    """요금제 정보"""
    name: str
    display_name: str
    price: int
    currency: str
    billing_period: str
    features: list[str]
    is_popular: bool


class PlansListResponse(CamelModel):
    """요금제 목록 응답"""
    plans: list[PlanInfo]
