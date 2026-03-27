import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.pulse import WeeklySnapshot, SegmentSnapshot, JobPosting, TalentPool, KeywordIndex
from app.models.ops import Company, Position


# Segment name mapping (fallback when no name in DB)
_SEGMENT_NAMES: dict[str, str] = {
    "backend": "백엔드",
    "frontend": "프론트엔드",
    "ml_ai": "ML/AI",
    "devops": "DevOps",
    "mobile": "모바일",
    "data": "데이터",
    "security": "보안",
    "fullstack": "풀스택",
}


def _segment_name(segment_id: str) -> str:
    return _SEGMENT_NAMES.get(segment_id, segment_id)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_sd_matrix(self, week: str | None = None) -> dict:
        """수급 매트릭스 데이터 — WeeklySnapshot + SegmentSnapshot"""
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

        return {
            "segments": segments,
            "total_demand": total_demand,
            "market_sd_ratio": market_sd,
            "week": week,
        }

    def get_company_rankings(self, segment_id: str | None = None, limit: int = 20) -> dict:
        """기업 순위 — JobPosting + Company"""
        q = (
            self.db.query(
                JobPosting.company_id,
                func.sum(JobPosting.count).label("total_count"),
            )
            .group_by(JobPosting.company_id)
        )
        if segment_id:
            q = q.filter(JobPosting.segment_id == segment_id)

        q = q.order_by(desc("total_count")).limit(limit)
        rows = q.all()

        if not rows:
            return {"companies": []}

        # Fetch company names in one query
        company_ids = [r.company_id for r in rows]
        companies_map = {
            str(c.id): c.name
            for c in self.db.query(Company).filter(Company.id.in_(company_ids)).all()
        }

        # Fetch segment_ids per company
        seg_rows = (
            self.db.query(JobPosting.company_id, JobPosting.segment_id)
            .filter(JobPosting.company_id.in_(company_ids))
            .distinct()
            .all()
        )
        seg_map: dict[str, list[str]] = {}
        for r in seg_rows:
            key = str(r.company_id)
            seg_map.setdefault(key, [])
            if r.segment_id not in seg_map[key]:
                seg_map[key].append(r.segment_id)

        companies = []
        for rank, r in enumerate(rows, start=1):
            cid = str(r.company_id)
            companies.append({
                "company_id": cid,
                "company_name": companies_map.get(cid, cid),
                "rank": rank,
                "posting_count": int(r.total_count),
                "segment_ids": seg_map.get(cid, []),
            })

        return {"companies": companies}

    def get_timeline(self, company_id: str | None = None) -> dict:
        """채용 타임라인 — JobPosting + Company (last 12 weeks)"""
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

        q = (
            self.db.query(
                JobPosting.company_id,
                JobPosting.week,
                func.sum(JobPosting.count).label("total_count"),
            )
            .filter(JobPosting.week.in_(self.db.query(weeks_subq)))
            .group_by(JobPosting.company_id, JobPosting.week)
        )
        if company_id:
            try:
                q = q.filter(JobPosting.company_id == uuid.UUID(company_id))
            except ValueError:
                return {"entries": []}

        rows = q.all()
        if not rows:
            return {"entries": []}

        company_ids = list({r.company_id for r in rows})
        companies_map = {
            str(c.id): c.name
            for c in self.db.query(Company).filter(Company.id.in_(company_ids)).all()
        }

        entries = [
            {
                "company_id": str(r.company_id),
                "company_name": companies_map.get(str(r.company_id), str(r.company_id)),
                "week": r.week,
                "count": int(r.total_count),
            }
            for r in rows
        ]

        return {"entries": entries}

    def get_trends(self, segment_id: str | None = None) -> dict:
        """트렌드 데이터 — WeeklySnapshot (last 12 weeks)"""
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

        return {"data_points": data_points}

    def get_company_profile(self, company_id: str) -> dict | None:
        """기업 프로필 — Company + JobPosting + Position"""
        try:
            cid_uuid = uuid.UUID(company_id)
        except ValueError:
            return None

        company = self.db.query(Company).filter(Company.id == cid_uuid).first()
        if not company:
            return None

        # Aggregate posting counts
        posting_agg = (
            self.db.query(
                JobPosting.week,
                func.sum(JobPosting.count).label("total_count"),
            )
            .filter(JobPosting.company_id == cid_uuid)
            .group_by(JobPosting.week)
            .order_by(JobPosting.week)
            .all()
        )

        hiring_trend = [
            {"week": r.week, "demand": int(r.total_count)}
            for r in posting_agg
        ]

        # Recent positions
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

        # OTW pct from latest TalentPool for company's segment
        otw_pct = 0.0
        if company.segment_id:
            tp = (
                self.db.query(TalentPool)
                .filter(TalentPool.segment_id == company.segment_id)
                .order_by(desc(TalentPool.week))
                .first()
            )
            if tp:
                otw_pct = float(tp.otw_pct)

        return {
            "company_id": company_id,
            "company_name": company.name,
            "segment_id": company.segment_id,
            "industry": company.industry,
            "hiring_trend": hiring_trend,
            "recent_postings": recent_postings,
            "otw_pct": otw_pct,
        }

    def get_resume_match_data(self, keywords: list[str], limit: int = 10) -> list[dict]:
        """이력서 매칭용 기업 + 키워드 데이터"""
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

        return [
            {
                "company_id": str(c.id),
                "company_name": c.name,
                "segment_id": seg_map.get(str(c.id), c.segment_id or ""),
                "industry": c.industry or "",
                "active_postings": posting_counts.get(str(c.id), 0),
            }
            for c in companies
        ]
