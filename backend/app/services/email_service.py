"""이메일 발송 서비스 모듈 (Resend SDK 기반).

API Key 미설정 시 graceful skip — 예외를 외부로 전파하지 않음.
SlackNotifier와 동일한 패턴 적용.
"""

import logging
from typing import List

import resend

from app.config import settings
from app.services.notification import notifier

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스 (Resend SDK 기반)."""

    def __init__(self) -> None:
        # API Key 설정 여부로 활성화 여부 결정
        self._enabled = bool(settings.RESEND_API_KEY)
        if self._enabled:
            resend.api_key = settings.RESEND_API_KEY
        else:
            logger.warning("RESEND_API_KEY 미설정 — 이메일 발송 비활성화")

    async def send_email(self, to: str, subject: str, html: str) -> bool:
        """단일 이메일 발송.

        Args:
            to: 수신자 이메일 주소
            subject: 이메일 제목
            html: HTML 본문

        Returns:
            발송 성공 여부 (API Key 미설정 시 False, 예외 없음)
        """
        # API Key 미설정 시 조용히 무시
        if not self._enabled:
            return False

        try:
            params: resend.Emails.SendParams = {
                "from": settings.RESEND_FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
            }
            resend.Emails.send(params)
            return True
        except Exception as e:  # noqa: BLE001
            logger.error("이메일 발송 실패: to=%s error=%s", to, e)
            # 실패 시 Slack 알림 (알림 실패도 예외 전파하지 않음)
            await notifier.send(f":warning: 이메일 발송 실패: {to} — {e}")
            return False

    async def send_batch(
        self,
        recipients: List[str],
        subject: str,
        html: str,
    ) -> dict:
        """배치 이메일 발송 — 100명 단위 청크.

        Args:
            recipients: 수신자 이메일 목록
            subject: 이메일 제목
            html: HTML 본문 (모든 수신자에게 동일한 내용)

        Returns:
            {"sent": int, "failed": int, "skipped": bool}
        """
        # API Key 미설정 시 조용히 무시
        if not self._enabled:
            return {"sent": 0, "failed": 0, "skipped": True}

        sent = 0
        failed = 0

        # 100명 단위 청크 분할 (Resend Batch API 한도)
        for i in range(0, len(recipients), 100):
            chunk = recipients[i : i + 100]
            params: List[resend.Emails.SendParams] = [
                {
                    "from": settings.RESEND_FROM_EMAIL,
                    "to": [recipient],
                    "subject": subject,
                    "html": html,
                }
                for recipient in chunk
            ]
            try:
                result: resend.Batch.SendResponse = resend.Batch.send(params)
                sent += len(result.get("data", []))
            except Exception as e:  # noqa: BLE001
                logger.error(
                    "배치 이메일 발송 실패: chunk_start=%d chunk_size=%d error=%s",
                    i,
                    len(chunk),
                    e,
                )
                failed += len(chunk)
                await notifier.send(
                    f":warning: 배치 이메일 발송 실패 (chunk {i}~{i + len(chunk)}): {e}"
                )

        return {"sent": sent, "failed": failed, "skipped": False}


# 모듈 레벨 싱글톤 인스턴스 — import 후 바로 사용 가능
email_service = EmailService()
