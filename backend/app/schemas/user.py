from datetime import datetime
from typing import Optional

from pydantic import field_validator

from app.schemas.common import CamelModel


class UserProfileResponse(CamelModel):
    """사용자 프로필 응답"""
    id: str
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    profile_image_url: str | None = None
    role: str = "USER"
    category: str | None = None
    status: str = "ACTIVE"
    organization_id: str | None = None
    last_login_at: datetime | None = None
    login_count: int = 0
    created_at: datetime | None = None


class UserProfileUpdate(CamelModel):
    """사용자 프로필 업데이트"""
    name: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    profile_image_url: str | None = None
    category: str | None = None


class PasswordChangeRequest(CamelModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("새 비밀번호는 최소 8자 이상이어야 합니다.")
        return v


class NotificationPreferences(CamelModel):
    """알림 설정"""
    weekly_report: Optional[bool] = None
    hiring_alert: Optional[bool] = None


class DeleteAccountRequest(CamelModel):
    """계정 삭제 요청 — 비밀번호 검증용"""
    current_password: str


class UsageStats(CamelModel):
    """사용량 통계"""
    daily_api_calls: dict = {}
    view_access: dict = {}
