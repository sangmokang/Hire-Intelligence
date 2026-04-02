from typing import Literal

from app.schemas.common import CamelModel


class ActionPanelContext(CamelModel):
    selected_segment: str | None = None
    current_data: dict | None = None
    user_category: str = "INHOUSE_HR"
    user_plan: str = "STARTER"


class ActionPanelRequest(CamelModel):
    view: str  # "sd-matrix" | "top-companies" | "timeline" | "trends" | "resume-match" | "company-analysis" | "market-signals"
    context: ActionPanelContext


class ActionItem(CamelModel):
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    text: str
    cta: str | None = None
    cta_url: str | None = None


class ActionPanelResponse(CamelModel):
    insight: str
    actions: list[ActionItem]
    related_views: list[str]
    is_ai_generated: bool = False  # True면 Claude API 사용, False면 rule-based
    locked: bool = False  # True면 플랜 업그레이드 필요
