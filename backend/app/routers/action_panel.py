from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.action_panel import ActionPanelRequest, ActionPanelResponse
from app.schemas.common import ApiResponse
from app.services.action_panel_service import ActionPanelService

router = APIRouter(prefix="/action-panel", tags=["action-panel"])


@router.post("", response_model=ApiResponse[ActionPanelResponse])
def generate_action_panel(
    request: ActionPanelRequest,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[ActionPanelResponse]:
    """Action Panel 생성 — view + context 기반 insight + actions 반환"""
    service = ActionPanelService()
    result = service.generate(request)
    return ApiResponse(data=result)
