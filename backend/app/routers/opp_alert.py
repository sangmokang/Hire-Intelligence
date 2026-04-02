"""OppAlert 라우터 — 헤드헌터 전용 BD 기회 감지 피드"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.opp_alert import OppAlertListResponse
from app.services.opp_alert_service import OppAlertService

router = APIRouter(prefix="/opp-alert", tags=["opp-alert"])


@router.get("", response_model=ApiResponse[OppAlertListResponse])
def get_opp_alerts(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OppAlertListResponse]:
    """OppAlert 피드 — 헤드헌터 전용 BD 기회 감지"""
    service = OppAlertService(db)
    result = service.get_opp_alerts(limit=limit)
    return ApiResponse(data=result)
