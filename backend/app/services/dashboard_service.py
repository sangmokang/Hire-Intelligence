import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.pulse import WeeklySnapshot, SegmentSnapshot, JobPosting, TalentPool, KeywordIndex, JdAnalysis
from app.models.ops import Company, Position
from app.constants.segments import SEGMENTS, LEGACY_TO_CANONICAL
from app.services.cache import cache_service


# 세그먼트 이름 매핑 — 표준 ID 기반으로 생성, 레거시 ID도 하위 호환 지원
_SEGMENT_NAMES: dict[str, str] = {s["id"]: s["name_ko"] for s in SEGMENTS}
# 레거시 ID가 아직 DB에 저장된 경우를 위해 레거시 → 표준 이름 매핑 추가
for _legacy_id, _canonical_id in LEGACY_TO_CANONICAL.items():
    if _legacy_id not in _SEGMENT_NAMES:
        _seg = next((s for s in SEGMENTS if s["id"] == _canonical_id), None)
        if _seg:
            _SEGMENT_NAMES[_legacy_id] = _seg["name_ko"]


def _segment_name(segment_id: str) -> str:
    # 레거시 ID가 들어올 경우 표준 ID로 변환 후 이름 조회
    canonical = LEGACY_TO_CANONICAL.get(segment_id, segment_id)
    return _SEGMENT_NAMES.get(canonical, _SEGMENT_NAMES.get(segment_id, segment_id))


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_sd_matrix(self, week: str | None = None) -> dict:
        """수급 매트릭스 데이터 — WeeklySnapshot + SegmentSnapshot"""
        # 캐시 확인 — week가 None이면 키를 "latest"로 통일
        _cache_key = f"dashboard_sd_matrix:{week or 'latest'}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        # Resolve target week
        if week is None:
            row = self.db.query(func.max(WeeklySnapshot.week)).scalar()
            week = row if row else ""

        if not week:
            return {"segments": [], "total_demand": 0, "market_sd_ratio": 1.0, "week": ""}

        # SegmentSnapshot for the week (richer data)
        snapshots = (
            self.db.query(SegmentSnapshot)
            .filter(SegmentSnapshot.week == week)
            .all()
        )

        # Fallback to WeeklySnapshot if SegmentSnapshot is empty
        if not snapshots:
            ws_rows = (
                self.db.query(WeeklySnapshot)
                .filter(WeeklySnapshot.week == week)
                .all()
            )
            segments = [
                {
                    "segment_id": r.segment_id,
                    "segment_name": _segment_name(r.segment_id),
                    "demand": r.demand,
                    "supply": r.supply,
                    "sd_ratio": float(r.sd_ratio),
                    "otw_pct": float(r.otw_pct),
                    "avg_salary": None,
                    "trend": None,
                }
                for r in ws_rows
            ]
        else:
            segments = [
                {
                    "segment_id": r.segment_id,
                    "segment_name": _segment_name(r.segment_id),
                    "demand": r.demand,
                    "supply": r.supply,
                    "sd_ratio": float(r.sd_ratio),
                    "otw_pct": float(r.otw_pct),
                    "avg_salary": r.avg_salary,
                    "trend": None,
                }
                for r in snapshots
            ]

        total_demand = sum(s["demand"] for s in segments)
        market_sd = (
            round(sum(s["sd_ratio"] for s in segments) / len(segments), 4)
            if segments else 1.0
        )

        _result = {
            "segments": segments,
            "total_demand": total_demand,
            "market_sd_ratio": market_sd,
            "week": week,
        }
        cache_service.set(_cache_key, _result, ttl=3600)
        return _result

    def get_company_rankings(self, segment_id: str | None = None, limit: int = 20) -> dict:
        """기업 순위 — JobPosting + Company (단일 JOIN 쿼리로 최적화)"""
        # 캐시 확인
        _cache_key = f"dashboard_company_rankings:{segment_id or 'all'}:{limit}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        # 단일 JOIN 쿼리: 3개 쿼리 → 1개 쿼리로 통합
        # func.array_agg(func.distinct(...)) — PostgreSQL 전용, Supabase OK
        q = (
            self.db.query(
                JobPosting.company_id,
                Company.name,
                func.sum(JobPosting.count).label("total_count"),
                func.array_agg(func.distinct(JobPosting.segment_id)).label("segment_ids"),
            )
            .join(Company, JobPosting.company_id == Company.id)
            .group_by(JobPosting.company_id, Company.name)
            .order_by(desc("total_count"))
            .limit(limit)
        )
        if segment_id:
            q = q.filter(JobPosting.segment_id == segment_id)

        rows = q.all()

        if not rows:
            return {"companies": []}

        companies = []
        for rank, r in enumerate(rows, start=1):
            cid = str(r.company_id)
            # array_agg 결과는 list 또는 None — None 방어 처리
            seg_ids: list[str] = r.segment_ids if r.segment_ids else []
            companies.append({
                "company_id": cid,
                "company_name": r.name or cid,
                "rank": rank,
                "posting_count": int(r.total_count),
                "segment_ids": seg_ids,
            })

        _result = {"companies": companies}
        cache_service.set(_cache_key, _result, ttl=3600)
        return _result

    def get_timeline(self, company_id: str | None = None) -> dict:
        """채용 타임라인 — JobPosting + Company (last 12 weeks)"""
        # 캐시 확인
        _cache_key = f"dashboard_timeline:{company_id or 'all'}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        # Determine the last 12 weeks
        max_week_row = self.db.query(func.max(JobPosting.week)).scalar()
        if not max_week_row:
            return {"entries": []}

        # Subquery: all distinct weeks ordered desc, limit 12
        weeks_subq = (
            self.db.query(JobPosting.week)
            .distinct()
            .order_by(desc(JobPosting.week))
            .limit(12)
            .subquery()
        )

        # 단일 JOIN 쿼리: 2개 쿼리 → 1개 쿼리로 통합 (Company 별도 조회 제거)
        q = (
            self.db.query(
                JobPosting.company_id,
                Company.name.label("company_name"),
                JobPosting.week,
                func.sum(JobPosting.count).label("total_count"),
            )
            .join(Company, JobPosting.company_id == Company.id)
            .filter(JobPosting.week.in_(self.db.query(weeks_subq)))
            .group_by(JobPosting.company_id, Company.name, JobPosting.week)
            .order_by(JobPosting.week, desc(func.sum(JobPosting.count)))
        )
        if company_id:
            try:
                q = q.filter(JobPosting.company_id == uuid.UUID(company_id))
            except ValueError:
                return {"entries": []}

        rows = q.all()
        if not rows:
            return {"entries": []}

        entries = [
            {
                "company_id": str(r.company_id),
                "company_name": r.company_name or str(r.company_id),
                "week": r.week,
                "count": int(r.total_count),
            }
            for r in rows
        ]

        _result = {"entries": entries}
        cache_service.set(_cache_key, _result, ttl=1800)
        return _result

    def get_trends(self, segment_id: str | None = None) -> dict:
        """트렌드 데이터 — WeeklySnapshot (last 12 weeks)"""
        # 캐시 확인
        _cache_key = f"dashboard_trends:{segment_id or 'all'}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        weeks_subq = (
            self.db.query(WeeklySnapshot.week)
            .distinct()
            .order_by(desc(WeeklySnapshot.week))
            .limit(12)
            .subquery()
        )

        q = (
            self.db.query(WeeklySnapshot)
            .filter(WeeklySnapshot.week.in_(self.db.query(weeks_subq)))
            .order_by(WeeklySnapshot.segment_id, WeeklySnapshot.week)
        )
        if segment_id:
            q = q.filter(WeeklySnapshot.segment_id == segment_id)

        rows = q.all()
        data_points = [
            {"week": r.week, "demand": r.demand, "segment_id": r.segment_id}
            for r in rows
        ]

        _result = {"data_points": data_points}
        cache_service.set(_cache_key, _result, ttl=3600)
        return _result

    def get_company_profile(self, company_id: str) -> dict | None:
        """기업 프로필 — Company + JobPosting + Position"""
        # 캐시 확인
        _cache_key = f"dashboard_company_profile:{company_id}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        try:
            cid_uuid = uuid.UUID(company_id)
        except ValueError:
            return None

        # Query 1: Company + JobPosting 주간 집계 JOIN (Company 단독 조회 + 집계 쿼리 통합)
        # Company 정보와 주간 채용 트렌드를 단일 JOIN으로 조회
        # Query 1: Company + JobPosting JOIN — 회사 정보와 주간 채용 집계를 한 번에 조회
        # Company 단독 조회(1개) + 집계 쿼리(1개) → 단일 JOIN(1개)으로 통합
        company_posting_rows = (
            self.db.query(
                Company.id,
                Company.name,
                Company.segment_id,
                Company.industry,
                JobPosting.week,
                func.sum(JobPosting.count).label("total_count"),
            )
            .join(JobPosting, Company.id == JobPosting.company_id, isouter=True)
            .filter(Company.id == cid_uuid)
            .group_by(Company.id, Company.name, Company.segment_id, Company.industry, JobPosting.week)
            .order_by(JobPosting.week)
            .all()
        )

        if not company_posting_rows:
            # JobPosting이 전혀 없는 경우 Company만 조회 (fallback)
            company = self.db.query(Company).filter(Company.id == cid_uuid).first()
            if not company:
                return None
            company_name = company.name
            company_segment_id = company.segment_id
            company_industry = company.industry
            hiring_trend: list[dict] = []
        else:
            first = company_posting_rows[0]
            company_name = first.name
            company_segment_id = first.segment_id
            company_industry = first.industry
            # week가 None인 행(JobPosting 없음)은 집계에서 제외
            hiring_trend = [
                {"week": r.week, "demand": int(r.total_count)}
                for r in company_posting_rows
                if r.week is not None
            ]

        # Query 2: Position — 최근 공고 10건 (ops 스키마, 분리 유지)
        recent_positions = (
            self.db.query(Position)
            .filter(Position.company_id == cid_uuid)
            .order_by(desc(Position.week))
            .limit(10)
            .all()
        )

        recent_postings = [
            {
                "title": p.title,
                "week": p.week,
                "platform": p.platform,
                "count": 1,
                "url": p.url,
            }
            for p in recent_positions
        ]

        # Query 3: TalentPool — pulse 스키마, 분리 유지
        otw_pct = 0.0
        if company_segment_id:
            tp = (
                self.db.query(TalentPool)
                .filter(TalentPool.segment_id == company_segment_id)
                .order_by(desc(TalentPool.week))
                .first()
            )
            if tp:
                otw_pct = float(tp.otw_pct)

        # Query 4 (pulse 스키마): JD 분석 데이터 — pulse 스키마, 분리 유지
        jd_analyses = (
            self.db.query(JdAnalysis)
            .filter(JdAnalysis.company_id == cid_uuid, JdAnalysis.parsed_at.isnot(None))
            .all()
        )

        jd_analysis_data = None
        if jd_analyses:
            # tech_profile 집계
            tech_freq: dict[str, int] = {}
            role_dist: dict[str, int] = {}
            for ja in jd_analyses:
                if ja.tech_stacks:
                    for t in ja.tech_stacks:
                        tech_freq[t] = tech_freq.get(t, 0) + 1
                if ja.role_level:
                    role_dist[ja.role_level] = role_dist.get(ja.role_level, 0) + 1

            jd_analysis_data = {
                "tech_profile": sorted(
                    [{"name": k, "count": v} for k, v in tech_freq.items()],
                    key=lambda x: x["count"], reverse=True
                )[:20],
                "role_distribution": role_dist,
                "jd_count": len(jd_analyses),
            }

        _result = {
            "company_id": company_id,
            "company_name": company_name,
            "segment_id": company_segment_id,
            "industry": company_industry,
            "hiring_trend": hiring_trend,
            "recent_postings": recent_postings,
            "otw_pct": otw_pct,
            "jd_analysis": jd_analysis_data,
        }
        cache_service.set(_cache_key, _result, ttl=1800)
        return _result

    def get_resume_match_data(self, keywords: list[str], limit: int = 10) -> list[dict]:
        """이력서 매칭용 기업 + 키워드 데이터"""
        # 캐시 확인 — 키워드 목록을 정렬 후 조인하여 키 생성
        _kw_key = ",".join(sorted(keywords)) if keywords else "none"
        _cache_key = f"dashboard_resume_match:{_kw_key}:{limit}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        # Find companies that appear in KeywordIndex for matched keywords
        if keywords:
            kw_lower = [kw.lower() for kw in keywords]
            ki_rows = (
                self.db.query(KeywordIndex.company_id, KeywordIndex.segment_id)
                .filter(
                    func.lower(KeywordIndex.keyword).in_(kw_lower),
                    KeywordIndex.company_id.isnot(None),
                )
                .distinct()
                .limit(limit * 2)
                .all()
            )
            company_ids = list({r.company_id for r in ki_rows if r.company_id})
            seg_map = {str(r.company_id): r.segment_id for r in ki_rows if r.company_id}
        else:
            company_ids = []
            seg_map = {}

        # Fallback: just pull recent companies from JobPosting
        if not company_ids:
            jp_rows = (
                self.db.query(JobPosting.company_id, JobPosting.segment_id)
                .distinct()
                .limit(limit)
                .all()
            )
            company_ids = [r.company_id for r in jp_rows]
            seg_map = {str(r.company_id): r.segment_id for r in jp_rows}

        if not company_ids:
            return []

        companies = (
            self.db.query(Company)
            .filter(Company.id.in_(company_ids[:limit]))
            .all()
        )

        # Active posting counts per company
        posting_counts = {
            str(r.company_id): int(r.cnt)
            for r in self.db.query(
                JobPosting.company_id,
                func.sum(JobPosting.count).label("cnt"),
            )
            .filter(JobPosting.company_id.in_(company_ids[:limit]))
            .group_by(JobPosting.company_id)
            .all()
        }

        _result = [
            {
                "company_id": str(c.id),
                "company_name": c.name,
                "segment_id": seg_map.get(str(c.id), c.segment_id or ""),
                "industry": c.industry or "",
                "active_postings": posting_counts.get(str(c.id), 0),
            }
            for c in companies
        ]
        cache_service.set(_cache_key, _result, ttl=1800)
        return _result

    def get_company_wow_changes(self, company_ids: list, current_week: str) -> dict[str, int]:
        """기업별 주간 채용 건수 변화량 계산 (이번 주 - 지난 주)"""
        # 캐시 확인 — company_ids 정렬 후 조인하여 키 생성
        _ids_key = ",".join(sorted(str(c) for c in company_ids))
        _cache_key = f"dashboard_wow_changes:{_ids_key}:{current_week}"
        _cached = cache_service.get(_cache_key)
        if _cached is not None:
            return _cached

        # ISO 주차 문자열(예: "2026-W13") → 이전 주차 문자열 계산
        try:
            year_str, week_str = current_week.split("-W")
            year, week_num = int(year_str), int(week_str)
        except (ValueError, AttributeError):
            return {}

        # 이전 주 계산: W01이면 전년도 마지막 주로 이동
        if week_num == 1:
            prev_year = year - 1
            # 전년도 마지막 주 번호 계산 (ISO 기준 52 또는 53주)
            dec_28 = date(prev_year, 12, 28)  # 12월 28일은 항상 해당 연도의 마지막 주에 속함
            prev_week_num = dec_28.isocalendar()[1]
            prev_week = f"{prev_year}-W{prev_week_num:02d}"
        else:
            prev_week = f"{year}-W{(week_num - 1):02d}"

        # 현재 주와 이전 주의 기업별 채용 건수 조회
        weeks = [current_week, prev_week]
        rows = (
            self.db.query(
                JobPosting.company_id,
                JobPosting.week,
                func.sum(JobPosting.count).label("total_count"),
            )
            .filter(
                JobPosting.company_id.in_(company_ids),
                JobPosting.week.in_(weeks),
            )
            .group_by(JobPosting.company_id, JobPosting.week)
            .all()
        )

        # 기업별 주차별 카운트 집계
        counts: dict[str, dict[str, int]] = {}
        for r in rows:
            cid = str(r.company_id)
            counts.setdefault(cid, {})
            counts[cid][r.week] = int(r.total_count)

        # 변화량 = 이번 주 - 지난 주 (데이터 없으면 0으로 처리)
        _result = {
            cid: counts[cid].get(current_week, 0) - counts[cid].get(prev_week, 0)
            for cid in counts
        }
        cache_service.set(_cache_key, _result, ttl=3600)
        return _result
