"""Slack Incoming Webhook 알림 유틸리티 모듈.

메인 로직(크롤러, DNA 갱신 등)의 실행 결과를 Slack으로 알림.
알림 실패는 메인 로직을 방해하지 않도록 예외를 외부로 전파하지 않음.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack Incoming Webhook을 통한 알림 전송 클래스."""

    def __init__(self, webhook_url: str | None = None) -> None:
        # webhook_url이 명시적으로 전달되지 않으면 settings에서 로드
        self._webhook_url = webhook_url if webhook_url is not None else settings.SLACK_WEBHOOK_URL

    async def send(self, text: str, blocks: list[dict] | None = None) -> bool:
        """Slack 메시지 전송.

        Args:
            text: 메시지 본문 (fallback 텍스트)
            blocks: Slack Block Kit 블록 목록 (선택)

        Returns:
            전송 성공 여부
        """
        # webhook_url이 설정되지 않으면 조용히 무시
        if not self._webhook_url:
            return False

        payload: dict = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self._webhook_url, json=payload)
                response.raise_for_status()
                return True
        except httpx.TimeoutException:
            logger.warning("Slack 알림 전송 타임아웃 (5초 초과)")
            return False
        except httpx.HTTPStatusError as e:
            logger.warning("Slack 알림 HTTP 오류: status=%s body=%s", e.response.status_code, e.response.text)
            return False
        except Exception as e:  # noqa: BLE001
            logger.warning("Slack 알림 전송 실패: %s", e)
            return False

    async def send_crawl_success(self, platform: str, count: int, week: str) -> bool:
        """크롤 성공 알림.

        Args:
            platform: 크롤 대상 플랫폼 (예: "wanted", "jobkorea")
            count: 수집된 JD 수
            week: 대상 주차 (예: "2024-W13")
        """
        text = f":white_check_mark: [{platform}] 크롤 완료 — {week} / {count}건 수집"
        return await self.send(text)

    async def send_crawl_failure(self, platform: str, error: str) -> bool:
        """크롤 실패 알림.

        Args:
            platform: 크롤 대상 플랫폼
            error: 오류 메시지
        """
        text = f":x: [{platform}] 크롤 실패 — {error}"
        return await self.send(text)

    async def send_data_quality_alert(self, issue: str, details: dict) -> bool:
        """데이터 품질 이상 알림.

        Args:
            issue: 이상 항목 요약 (예: "null_rate_high")
            details: 상세 정보 딕셔너리
        """
        detail_lines = "\n".join(f"  • {k}: {v}" for k, v in details.items())
        text = f":warning: 데이터 품질 경고 — {issue}\n{detail_lines}"
        return await self.send(text)

    async def send_dna_refresh_result(self, week: str, success: bool, detail: str) -> bool:
        """DNA 갱신 결과 알림.

        Args:
            week: 갱신 대상 주차 (예: "2024-W13")
            success: 갱신 성공 여부
            detail: 결과 상세 메시지
        """
        icon = ":dna: :white_check_mark:" if success else ":dna: :x:"
        status = "성공" if success else "실패"
        text = f"{icon} DNA 갱신 {status} — {week}\n{detail}"
        return await self.send(text)


# 모듈 레벨 싱글톤 인스턴스 — import 후 바로 사용 가능
notifier = SlackNotifier()
