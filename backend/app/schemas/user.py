from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class UserProfileResponse(BaseModel):
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


class UserProfileUpdate(BaseModel):
    """사용자 프로필 업데이트"""
    name: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    profile_image_url: str | None = None
    category: str | None = None
