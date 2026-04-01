"""
Sprint 5 이메일 서비스 테스트
- EmailService: send_email, send_batch, API Key 미설정 처리
- email_templates: weekly_report_template, welcome_template
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# EmailService 테스트
# ---------------------------------------------------------------------------

class TestEmailServiceNoApiKey:
    def test_send_email_no_api_key_returns_false(self):
        """RESEND_API_KEY 미설정 시 send_email → False 반환 (예외 없음)"""
        import asyncio
        from app.services.email_service import EmailService

        svc = EmailService.__new__(EmailService)
        svc._enabled = False  # API Key 없음 상태 직접 설정

        result = asyncio.run(svc.send_email("user@test.com", "제목", "<p>내용</p>"))

        assert result is False, "API Key 없을 때 False를 반환해야 함"

    def test_send_batch_no_api_key_returns_skipped(self):
        """RESEND_API_KEY 미설정 시 send_batch → skipped=True"""
        import asyncio
        from app.services.email_service import EmailService

        svc = EmailService.__new__(EmailService)
        svc._enabled = False  # API Key 없음 상태 직접 설정

        result = asyncio.run(
            svc.send_batch(["user1@test.com", "user2@test.com"], "제목", "<p>내용</p>")
        )

        assert result["skipped"] is True, "API Key 없을 때 skipped=True여야 함"
        assert result["sent"] == 0
        assert result["failed"] == 0


class TestEmailServiceWithApiKey:
    def test_send_email_success_returns_true(self):
        """send_email — resend.Emails.send mock → True 반환"""
        import asyncio
        from app.services.email_service import EmailService

        svc = EmailService.__new__(EmailService)
        svc._enabled = True

        with patch("resend.Emails.send", return_value={"id": "email-123"}) as mock_send, \
             patch("app.config.settings") as mock_settings:
            mock_settings.RESEND_FROM_EMAIL = "noreply@hire-intelligence.co.kr"
            result = asyncio.run(svc.send_email("user@test.com", "테스트 제목", "<p>테스트</p>"))

        assert result is True, "발송 성공 시 True를 반환해야 함"
        mock_send.assert_called_once()


# ---------------------------------------------------------------------------
# 이메일 템플릿 테스트
# ---------------------------------------------------------------------------

class TestEmailTemplates:
    def test_weekly_report_template_returns_html(self):
        """weekly_report_template → 유효한 HTML 문자열 반환"""
        from app.services.email_templates import weekly_report_template

        data = {
            "week": "2026-W14",
            "top_companies": [
                {"name": "카카오", "jd_count": 42, "change": 5},
                {"name": "네이버", "jd_count": 38, "change": -2},
            ],
            "sd_summary": {"excess_count": 3, "balanced_count": 10, "shortage_count": 2},
            "trends": [
                {"skill": "Python", "change_pct": 12.5},
                {"skill": "Kubernetes", "change_pct": -3.2},
            ],
        }

        html = weekly_report_template(data)

        assert isinstance(html, str), "HTML 문자열이어야 함"
        assert "<!DOCTYPE html>" in html, "DOCTYPE 선언이 포함되어야 함"
        assert "2026-W14" in html, "주차 정보가 포함되어야 함"
        assert "카카오" in html, "기업명이 포함되어야 함"
        assert "Python" in html, "스킬 트렌드가 포함되어야 함"

    def test_welcome_template_returns_html(self):
        """welcome_template → 유효한 HTML 문자열 반환"""
        from app.services.email_templates import welcome_template

        html = welcome_template("홍길동")

        assert isinstance(html, str), "HTML 문자열이어야 함"
        assert "<!DOCTYPE html>" in html, "DOCTYPE 선언이 포함되어야 함"
        assert "홍길동" in html, "사용자 이름이 포함되어야 함"
        assert "Hire Intelligence" in html, "브랜드명이 포함되어야 함"
