from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.tds_simulator import TdsSimulatorRequest, TdsSimulatorResponse
from app.services.tds_simulator_service import TdsSimulatorService

router = APIRouter(prefix="/tds-simulator", tags=["tds-simulator"])


@router.post("", response_model=ApiResponse[TdsSimulatorResponse])
def simulate_tds(
    request: TdsSimulatorRequest,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[TdsSimulatorResponse]:
    """TDS 시뮬레이터 — 채용 조직 인재 밀도 점수 시뮬레이션 (CHRO 전용)"""
    service = TdsSimulatorService()
    result = service.simulate(request)
    return ApiResponse(data=result)
