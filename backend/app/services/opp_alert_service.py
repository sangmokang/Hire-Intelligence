"""OppAlert 서비스 — 헤드헌터 전용 BD 기회 감지"""
import uuid as uuid_mod
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ops import Company
from app.models.pulse import JobPosting, WeeklySnapshot, SegmentSnapshot
from app.schemas.opp_alert import OppAlertItem, OppAlertListResponse, OppAlertTrigger


def _calculate_opp_score(active_postings: int, hiring_weeks: int, sd_ratio: float) -> float:
    """OppScore 산출 (PRD 기준)"""
    otw_score = 0  # OTW 데이터 없으면 0
    hiring_score = min(active_postings * 2, 25)
    sd_score = max(0, (1 - sd_ratio) * 25) if sd_ratio < 1.0 else 0
    tenure_score = min(hiring_weeks * 2.5, 20)
    return min(100.0, otw_score + hiring_score + sd_score + tenure_score)


def _priority_from_score(score: float) -> str | None:
    """점수 → priority 변환 (30점 미만은 None 반환 → 제외)"""
    if score >= 70:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return None


class OppAlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_opp_alerts(self, limit: int = 50) -> OppAlertListResponse:
        """OppScore 30점 이상 기업 목록 반환 (점수 내림차순, 최대 limit개)"""
        generated_at = datetime.now(timezone.utc).isoformat()

        try:
            # 최신 week 기준 조회
            latest_week: str | None = self.db.query(func.max(WeeklySnapshot.week)).scalar()
            if not latest_week:
                return OppAlertListResponse(items=[], total=0, generated_at=generated_at)

            # 세그먼트별 최신 S/D Ratio 매핑
            segment_rows = (
                self.db.query(SegmentSnapshot.segment_id, SegmentSnapshot.sd_ratio)
                .filter(SegmentSnapshot.week == latest_week)
                .all()
            )
            seg_sd: dict[str, float] = {row.segment_id: float(row.sd_ratio) for row in segment_rows}

            # 기업별 최신 week 공고 집계 (company_id, segment_id, count 합계)
            posting_rows = (
                self.db.query(
                    JobPosting.company_id,
                    JobPosting.segment_id,
                    func.sum(JobPosting.count).label("total_count"),
                )
                .filter(JobPosting.week == latest_week)
                .group_by(JobPosting.company_id, JobPosting.segment_id)
                .all()
            )

            if not posting_rows:
                return OppAlertListResponse(items=[], total=0, generated_at=generated_at)

            # 기업별 공고 집계 (company_id → {segment_id, total_count})
            company_data: dict[str, dict] = {}
            for row in posting_rows:
                cid = str(row.company_id)
                if cid not in company_data or row.total_count > company_data[cid]["count"]:
                    company_data[cid] = {
                        "segment_id": row.segment_id,
                        "count": int(row.total_count or 0),
                    }

            if not company_data:
                return OppAlertListResponse(items=[], total=0, generated_at=generated_at)

            # 기업 ID 목록 조회 (이름 매핑)
            company_ids = list(company_data.keys())

            # UUID 변환
            uuid_list = []
            for cid in company_ids:
                try:
                    uuid_list.append(uuid_mod.UUID(cid))
                except ValueError:
                    continue

            company_rows = (
                self.db.query(Company.id, Company.name, Company.segment_id)
                .filter(Company.id.in_(uuid_list))
                .all()
            )
            company_name_map: dict[str, str] = {str(row.id): row.name for row in company_rows}
            company_segment_map: dict[str, str] = {
                str(row.id): (row.segment_id or "") for row in company_rows
            }

            # 기업별 연속 채용 주차 수 계산
            # JobPosting 에서 company_id별 distinct week 수로 근사
            hiring_weeks_rows = (
                self.db.query(
                    JobPosting.company_id,
                    func.count(func.distinct(JobPosting.week)).label("week_count"),
                )
                .filter(JobPosting.company_id.in_(uuid_list))
                .group_by(JobPosting.company_id)
                .all()
            )
            hiring_weeks_map: dict[str, int] = {
                str(row.company_id): int(row.week_count) for row in hiring_weeks_rows
            }

            # OppScore 계산 및 필터링
            items: list[OppAlertItem] = []
            for cid, data in company_data.items():
                segment_id = company_segment_map.get(cid) or data["segment_id"] or ""
                sd_ratio = seg_sd.get(segment_id, 1.0)
                active_postings = data["count"]
                hiring_weeks = hiring_weeks_map.get(cid, 1)

                score = _calculate_opp_score(active_postings, hiring_weeks, sd_ratio)
                priority = _priority_from_score(score)
                if priority is None:
                    continue

                company_name = company_name_map.get(cid, cid)
                items.append(
                    OppAlertItem(
                        id=cid,
                        company_id=cid,
                        company_name=company_name,
                        segment=segment_id,
                        opp_score=round(score, 1),
                        priority=priority,
                        triggers=OppAlertTrigger(
                            otw_increase=0.0,   # OTW 데이터 없음
                            new_postings=active_postings,
                            hiring_weeks=hiring_weeks,
                            sd_ratio=round(sd_ratio, 4),
                        ),
                        detected_at=generated_at,
                    )
                )

            # 점수 내림차순 정렬
            items.sort(key=lambda x: x.opp_score, reverse=True)
            items = items[:limit]

            return OppAlertListResponse(
                items=items,
                total=len(items),
                generated_at=generated_at,
            )

        except Exception as exc:
            # DB 오류 시 graceful empty response
            import logging
            logging.getLogger(__name__).warning("OppAlertService error: %s", exc)
            return OppAlertListResponse(items=[], total=0, generated_at=generated_at)
