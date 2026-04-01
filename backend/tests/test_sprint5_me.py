"""
Sprint 5 /me 엔드포인트 통합 테스트
- POST /me/password, GET/PATCH /me/notifications, DELETE /me, GET /me/usage, GET /me/report/preview
- conftest.py의 authed_client, pro_client, mock_db, mock_supabase 픽스처 활용

주의: conftest의 mock_user id가 "test-uuid" (유효하지 않은 UUID)이므로
UserService.get_profile()에서 ValueError → None 반환됨.
따라서 get_profile/update_profile 경로는 UserService 전체를 patch하는 방식 사용.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_profile_mock(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    notification_preferences: dict | None = None,
    usage_stats: dict | None = None,
    status: str = "ACTIVE",
):
    """UserProfile ORM 모사 객체 생성"""
    profile = MagicMock()
    profile.id = user_id
    profile.name = "테스트 유저"
    profile.phone = None
    profile.company = None
    profile.job_title = None
    profile.profile_image_url = None
    profile.role = "USER"
    profile.category = None
    profile.status = status
    profile.organization_id = None
    profile.last_login_at = None
    profile.login_count = 0
    profile.created_at = None
    profile.notification_preferences = notification_preferences or {"weekly_report": True, "hiring_alert": True}
    profile.usage_stats = usage_stats
    return profile


# ---------------------------------------------------------------------------
# 1. POST /me/password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_success(self, authed_client: TestClient, mock_db, mock_supabase):
        """POST /me/password 성공 → 200, message 반환"""
        profile = _make_profile_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        with patch("app.dependencies.get_supabase_anon_client") as mock_anon_factory:
            anon_mock = MagicMock()
            anon_mock.auth.sign_in_with_password.return_value = MagicMock()
            mock_anon_factory.return_value = anon_mock
            mock_supabase.auth.admin.update_user_by_id.return_value = MagicMock()

            resp = authed_client.post(
                "/api/v1/me/password",
                json={"currentPassword": "old_password", "newPassword": "new_password123"},
            )

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] is not None

    def test_change_password_wrong_current(self, authed_client: TestClient, mock_db, mock_supabase):
        """POST /me/password — 현재 비밀번호 불일치 → 401"""
        profile = _make_profile_mock()
        mock_db.query.return_value.filter.return_value.first.return_value = profile

        with patch("app.dependencies.get_supabase_anon_client") as mock_anon_factory:
            anon_mock = MagicMock()
            anon_mock.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
            mock_anon_factory.return_value = anon_mock

            resp = authed_client.post(
                "/api/v1/me/password",
                json={"currentPassword": "wrong_password", "newPassword": "new_password123"},
            )

        assert resp.status_code == 401, f"응답: {resp.json()}"

    def test_change_password_short_new_password(self, authed_client: TestClient, mock_db, mock_supabase):
        """POST /me/password — 새 비밀번호 8자 미만 → 422 validation error"""
        resp = authed_client.post(
            "/api/v1/me/password",
            json={"currentPassword": "old_password", "newPassword": "short"},
        )
        assert resp.status_code == 422, f"응답: {resp.json()}"


# ---------------------------------------------------------------------------
# 2. GET /me/notifications
# ---------------------------------------------------------------------------

class TestGetNotifications:
    def test_get_notifications_success(self, authed_client: TestClient, mock_db):
        """GET /me/notifications → 200, JSON 알림 설정 반환"""
        expected_prefs = {"weekly_report": True, "hiring_alert": False}

        with patch("app.services.user_service.UserService.get_notification_preferences") as mock_prefs:
            mock_prefs.return_value = expected_prefs
            resp = authed_client.get("/api/v1/me/notifications")

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body
        assert isinstance(body["data"], dict)


# ---------------------------------------------------------------------------
# 3. PATCH /me/notifications
# ---------------------------------------------------------------------------

class TestUpdateNotifications:
    def test_update_notifications_success(self, authed_client: TestClient, mock_db):
        """PATCH /me/notifications → 200, 부분 업데이트 반영"""
        merged_prefs = {"weekly_report": False, "hiring_alert": True}

        with patch("app.services.user_service.UserService.update_notification_preferences") as mock_update:
            mock_update.return_value = merged_prefs
            resp = authed_client.patch(
                "/api/v1/me/notifications",
                json={"weeklyReport": False},
            )

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        assert "data" in body

    def test_update_notifications_extra_fields_ignored(self, authed_client: TestClient, mock_db):
        """PATCH /me/notifications — 알 수 없는 필드 포함 시 무시 또는 422"""
        with patch("app.services.user_service.UserService.update_notification_preferences") as mock_update:
            mock_update.return_value = {"weekly_report": True, "hiring_alert": True}
            resp = authed_client.patch(
                "/api/v1/me/notifications",
                json={"unknownField": "some_value"},
            )

        # Pydantic extra="ignore" 시 200, extra="forbid" 시 422 — 둘 다 허용
        assert resp.status_code in (200, 422), f"예상치 못한 상태코드: {resp.status_code}"


# ---------------------------------------------------------------------------
# 4. DELETE /me
# ---------------------------------------------------------------------------

class TestDeleteAccount:
    def test_delete_account_success(self, authed_client: TestClient, mock_db, mock_supabase):
        """DELETE /me → 200, soft delete 성공"""
        with patch("app.services.user_service.UserService.delete_account", new_callable=AsyncMock) as mock_del, \
             patch("app.dependencies.get_supabase_anon_client") as mock_anon:
            mock_del.return_value = None
            mock_anon.return_value.auth.sign_in_with_password.return_value = None
            resp = authed_client.request("DELETE", "/api/v1/me", json={"currentPassword": "password123"})

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] is not None

    def test_delete_account_not_found(self, authed_client: TestClient, mock_db, mock_supabase):
        """DELETE /me — 프로필 없을 때 404"""
        from fastapi import HTTPException, status as http_status

        with patch("app.services.user_service.UserService.delete_account", new_callable=AsyncMock) as mock_del, \
             patch("app.dependencies.get_supabase_anon_client") as mock_anon:
            mock_del.side_effect = HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="프로필을 찾을 수 없습니다.",
            )
            mock_anon.return_value.auth.sign_in_with_password.return_value = None
            resp = authed_client.request("DELETE", "/api/v1/me", json={"currentPassword": "password123"})

        assert resp.status_code == 404, f"응답: {resp.json()}"


# ---------------------------------------------------------------------------
# 5. GET /me/usage
# ---------------------------------------------------------------------------

class TestGetUsage:
    def test_get_usage_with_data(self, authed_client: TestClient, mock_db):
        """GET /me/usage — 사용량 데이터 있을 때 200"""
        from datetime import datetime, timezone, timedelta
        today = datetime.now(timezone.utc).date()
        date_str = str(today - timedelta(days=1))

        usage_data = {
            "daily_api_calls": {date_str: 5},
            "view_access": {"sd_matrix": 3, "trends": 2},
        }

        with patch("app.services.user_service.UserService.get_usage_stats") as mock_stats:
            mock_stats.return_value = usage_data
            resp = authed_client.get("/api/v1/me/usage")

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        assert "dailyApiCalls" in data or "daily_api_calls" in data
        assert "viewAccess" in data or "view_access" in data

    def test_get_usage_empty_data(self, authed_client: TestClient, mock_db):
        """GET /me/usage — 사용량 데이터 없을 때 200, 빈 구조 반환"""
        with patch("app.services.user_service.UserService.get_usage_stats") as mock_stats:
            mock_stats.return_value = {"daily_api_calls": {}, "view_access": {}}
            resp = authed_client.get("/api/v1/me/usage")

        assert resp.status_code == 200, f"응답: {resp.json()}"
        body = resp.json()
        assert body["status"] == "success"
        data = body["data"]
        daily = data.get("dailyApiCalls") or data.get("daily_api_calls") or {}
        views = data.get("viewAccess") or data.get("view_access") or {}
        assert daily == {}
        assert views == {}


# ---------------------------------------------------------------------------
# 6. GET /me/report/preview
# ---------------------------------------------------------------------------

class TestReportPreview:
    def test_report_preview_pro_success(self, pro_client: TestClient, mock_db):
        """GET /me/report/preview — PRO 사용자 → 200, HTML 반환"""
        with patch("app.services.report_service.ReportService.get_report_data") as mock_data, \
             patch("app.services.report_service.ReportService.generate_weekly_report_html") as mock_html:
            mock_data.return_value = {
                "week": "2026-W14",
                "top_companies": [],
                "sd_summary": {"excess_count": 0, "balanced_count": 0, "shortage_count": 0},
                "trends": [],
            }
            mock_html.return_value = "<html><body>테스트 리포트</body></html>"

            resp = pro_client.get("/api/v1/me/report/preview")

        assert resp.status_code == 200, f"응답: {resp.text}"
        assert "html" in resp.headers.get("content-type", "").lower() or "<html" in resp.text.lower()

    def test_report_preview_starter_forbidden(self, authed_client: TestClient, mock_db):
        """GET /me/report/preview — STARTER 사용자 → 403"""
        resp = authed_client.get("/api/v1/me/report/preview")
        assert resp.status_code == 403, f"응답: {resp.json()}"
