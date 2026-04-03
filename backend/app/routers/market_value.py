from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.market_value import MarketValueRequest, MarketValueResponse
from app.services.market_value_service import MarketValueService

router = APIRouter(prefix="/market-value", tags=["market-value"])


@router.post("", response_model=ApiResponse[MarketValueResponse])
def calculate_market_value(
    request: MarketValueRequest,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[MarketValueResponse]:
    """시장가치 계산 — 스킬/경력/학력 기반 연봉 시장가치 (JOB_SEEKER 전용)"""
    service = MarketValueService()
    result = service.calculate(request)
    return ApiResponse(data=result)
