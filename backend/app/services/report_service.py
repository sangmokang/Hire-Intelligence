"""주간 리포트 생성 및 발송 서비스."""

import datetime
import logging

from sqlalchemy.orm import Session

from app.dependencies import get_supabase_client
from app.services.email_service import email_service
from app.services.email_templates import weekly_report_template
from app.services.notification import notifier

logger = logging.getLogger(__name__)


class ReportService:
    """주간 리포트 생성 서비스."""

    def get_report_data(self, db: Session) -> dict:
        """주간 리포트 데이터 수집.

        DashboardService에서 SD Matrix, Top Companies, Trends 데이터를 가져옴.
        이미 캐시된 데이터를 활용하므로 별도 캐싱 불필요.
        """
        from app.services.dashboard_service import DashboardService

        dashboard = DashboardService(db)

        # 최신 주차 기준 SD Matrix 수집
        sd_data = dashboard.get_sd_matrix()
        week: str = sd_data.get("week", "")

        # 수급 매트릭스 요약 — excess/balanced/shortage 카운트
        segments = sd_data.get("segments", [])
        excess_count = sum(1 for s in segments if s.get("sd_ratio", 1.0) > 1.2)
        balanced_count = sum(1 for s in segments if 0.8 <= s.get("sd_ratio", 1.0) <= 1.2)
        shortage_count = sum(1 for s in segments if s.get("sd_ratio", 1.0) < 0.8)
        sd_summary = {
            "excess_count": excess_count,
            "balanced_count": balanced_count,
            "shortage_count": shortage_count,
        }

        # Top 5 기업 — company_rankings + WoW 변화량
        rankings_data = dashboard.get_company_rankings(limit=5)
        companies_raw = rankings_data.get("companies", [])

        top_companies: list[dict] = []
        if companies_raw and week:
            company_ids = [c["company_id"] for c in companies_raw]
            wow_changes = dashboard.get_company_wow_changes(
                company_ids=company_ids, current_week=week
            )
            for c in companies_raw:
                top_companies.append(
                    {
                        "name": c.get("company_name", ""),
                        "jd_count": c.get("posting_count", 0),
                        "change": wow_changes.get(c["company_id"], 0),
                    }
                )
        else:
            top_companies = [
                {
                    "name": c.get("company_name", ""),
                    "jd_count": c.get("posting_count", 0),
                    "change": 0,
                }
                for c in companies_raw
            ]

        # 주간 스킬 트렌드 — WeeklySnapshot demand 변화를 트렌드로 표현
        trends_data = dashboard.get_trends()
        data_points = trends_data.get("data_points", [])

        # 세그먼트별로 최신 2개 주차를 비교해 change_pct 계산
        seg_weeks: dict[str, list[dict]] = {}
        for dp in data_points:
            seg_id = dp["segment_id"]
            seg_weeks.setdefault(seg_id, [])
            seg_weeks[seg_id].append(dp)

        trends: list[dict] = []
        for seg_id, points in seg_weeks.items():
            # 최신 주차 순 정렬
            sorted_points = sorted(points, key=lambda x: x["week"], reverse=True)
            if len(sorted_points) >= 2:
                latest_demand = sorted_points[0]["demand"] or 0
                prev_demand = sorted_points[1]["demand"] or 0
                if prev_demand > 0:
                    change_pct = (latest_demand - prev_demand) / prev_demand * 100
                else:
                    change_pct = 0.0
            elif len(sorted_points) == 1:
                change_pct = 0.0
            else:
                continue
            trends.append({"skill": seg_id, "change_pct": round(change_pct, 1)})

        # 변화율 절댓값 기준 정렬 — 가장 주목할 만한 트렌드 상위 5개
        trends.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

        return {
            "week": week,
            "top_companies": top_companies[:5],
            "sd_summary": sd_summary,
            "trends": trends[:5],
        }

    def generate_weekly_report_html(self, data: dict) -> str:
        """weekly_report_template으로 HTML 생성."""
        return weekly_report_template(data)

    async def send_weekly_reports(self, db: Session) -> dict:
        """주간 리포트 이메일 배치 발송.

        1. notification_preferences.weekly_report=true인 사용자 조회
        2. 리포트 데이터 수집 (한 번만)
        3. HTML 생성
        4. email_service.send_batch로 배치 발송
        5. 결과 Slack 알림
        """
        from app.models.user import UserProfile, UserStatus

        # weekly_report 수신 동의 사용자 조회
        # notification_preferences가 NULL이면 기본값(weekly_report=True)으로 처리
        profiles = (
            db.query(UserProfile)
            .filter(
                UserProfile.status == UserStatus.ACTIVE,
            )
            .all()
        )

        # Supabase admin API로 모든 활성 사용자 이메일 조회 — {user_id: email} 매핑
        supabase = get_supabase_client()
        auth_users = supabase.auth.admin.list_users()
        email_map: dict[str, str] = {
            str(u.id): u.email for u in auth_users if u.email
        }

        # 수신 동의 사용자만 필터링 — notification_preferences가 None이면 기본값 True
        recipients: list[str] = []
        for profile in profiles:
            prefs = profile.notification_preferences or {}
            if prefs.get("weekly_report", True):
                email = email_map.get(str(profile.user_id))
                if email:
                    recipients.append(email)

        # 리포트 데이터 수집 (한 번만)
        report_data = self.get_report_data(db)
        week = report_data.get("week", "")

        # HTML 생성
        html = self.generate_weekly_report_html(report_data)
        subject = f"[Hire Intelligence] 주간 채용 트렌드 리포트 {week}"

        # 배치 발송 — recipients가 비어있으면 0건 처리
        result = {"sent": 0, "failed": 0, "skipped": not bool(recipients)}
        if recipients:
            result = await email_service.send_batch(
                recipients=recipients,
                subject=subject,
                html=html,
            )

        # 결과 Slack 알림
        sent = result.get("sent", 0)
        failed = result.get("failed", 0)
        skipped = result.get("skipped", False)

        if skipped:
            await notifier.send(
                f":email: 주간 리포트 발송 건너뜀 (RESEND_API_KEY 미설정 또는 수신자 없음) — {week}"
            )
        else:
            status_icon = ":white_check_mark:" if failed == 0 else ":warning:"
            await notifier.send(
                f"{status_icon} 주간 리포트 발송 완료 — {week} / 성공: {sent}건 / 실패: {failed}건"
            )

        logger.info(f"주간 리포트 발송 결과: week={week} sent={sent} failed={failed} skipped={skipped}")
        return result


# 모듈 레벨 싱글톤 인스턴스
report_service = ReportService()
