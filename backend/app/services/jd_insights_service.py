"""JD 인사이트 서비스 — 기술 트렌드, 경력 분포, 연봉 벤치마크 집계"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, select

from app.models.pulse import JdAnalysis
from app.constants.segments import get_segment_name

logger = logging.getLogger(__name__)


class JdInsightsService:
    def __init__(self, db: Session):
        self.db = db

    def get_insights(self, segment_id: str | None = None, weeks: int = 12) -> dict:
        """JD 인사이트 조회 — 기술 트렌드, 경력 분포, 연봉 벤치마크"""

        # 최근 N주 데이터 범위
        recent_weeks_subq = (
            self.db.query(JdAnalysis.week)
            .filter(JdAnalysis.parsed_at.isnot(None))
            .distinct()
            .order_by(desc(JdAnalysis.week))
            .limit(weeks)
            .subquery()
        )

        # 기본 쿼리 (파싱 완료된 레코드만)
        base_q = (
            self.db.query(JdAnalysis)
            .filter(
                JdAnalysis.parsed_at.isnot(None),
                JdAnalysis.week.in_(select(recent_weeks_subq.c.week)),
            )
        )
        if segment_id:
            base_q = base_q.filter(JdAnalysis.segment_id == segment_id)

        analyses = base_q.all()

        if not analyses:
            return {
                "tech_trends": [],
                "experience_distribution": [],
                "salary_benchmarks": [],
                "top_domain_tags": [],
                "total_analyzed": 0,
            }

        # 1. 기술 스택 트렌드 (상위 20개)
        tech_counts: dict[str, int] = {}
        for a in analyses:
            if a.tech_stacks:
                for tech in a.tech_stacks:
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1

        tech_trends = sorted(
            [{"name": k, "count": v, "previous_count": 0, "change": 0} for k, v in tech_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:20]

        # 2. 경력 수준 분포
        level_counts: dict[str, int] = {}
        for a in analyses:
            if a.role_level:
                level_counts[a.role_level] = level_counts.get(a.role_level, 0) + 1

        total_with_level = sum(level_counts.values()) or 1
        experience_distribution = [
            {
                "level": level,
                "count": count,
                "percentage": round(count / total_with_level * 100, 1),
            }
            for level, count in sorted(level_counts.items())
        ]

        # 3. 세그먼트별 연봉 벤치마크 (min/max 분리 집계)
        salary_mins_by_seg: dict[str, list[int]] = {}
        salary_maxs_by_seg: dict[str, list[int]] = {}
        for a in analyses:
            if a.salary_min is not None or a.salary_max is not None:
                seg = a.segment_id
                if a.salary_min:
                    salary_mins_by_seg.setdefault(seg, []).append(a.salary_min)
                if a.salary_max:
                    salary_maxs_by_seg.setdefault(seg, []).append(a.salary_max)

        all_seg_ids = set(salary_mins_by_seg) | set(salary_maxs_by_seg)
        salary_benchmarks = []
        for seg in sorted(all_seg_ids):
            mins = salary_mins_by_seg.get(seg, [])
            maxs = salary_maxs_by_seg.get(seg, [])
            avg_min = round(sum(mins) / len(mins)) if mins else None
            avg_max = round(sum(maxs) / len(maxs)) if maxs else None
            # 평균 연봉 = (avg_min + avg_max) / 2, 한쪽만 있으면 그 값 사용
            if avg_min is not None and avg_max is not None:
                salary_avg = round((avg_min + avg_max) / 2)
            else:
                salary_avg = avg_min or avg_max
            salary_benchmarks.append({
                "segment_id": seg,
                "segment_name": get_segment_name(seg),
                "salary_min": min(mins) if mins else None,
                "salary_max": max(maxs) if maxs else None,
                "salary_avg": salary_avg,
                "sample_count": len(mins) + len(maxs),
            })

        # 4. 도메인 태그 상위
        domain_counts: dict[str, int] = {}
        for a in analyses:
            if a.domain_tags:
                for tag in a.domain_tags:
                    domain_counts[tag] = domain_counts.get(tag, 0) + 1

        top_domain_tags = sorted(
            [{"name": k, "count": v} for k, v in domain_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        return {
            "tech_trends": tech_trends,
            "experience_distribution": experience_distribution,
            "salary_benchmarks": salary_benchmarks,
            "top_domain_tags": top_domain_tags,
            "total_analyzed": len(analyses),
        }
