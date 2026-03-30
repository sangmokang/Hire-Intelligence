"""회사 DNA 프로필 계산 및 조회 서비스"""
import logging
import math
import uuid
from collections import Counter
from decimal import Decimal

from sqlalchemy import func, desc, distinct, case, and_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.ops import Company
from app.models.pulse import JdAnalysis, CompanyDnaSnapshot, JobPosting

logger = logging.getLogger(__name__)


class CompanyDnaService:
    """회사 DNA 프로필 계산 및 조회 서비스"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    #  세그먼트 결정
    # ------------------------------------------------------------------ #

    def resolve_segment_id(self, company_id: uuid.UUID) -> str | None:
        """세그먼트 결정 규칙 (ADR-2):
        1. 최근 12주 jd_analyses에서 가장 많은 COUNT(*)를 가진 segment_id
        2. 없으면 Company.segment_id
        3. 둘 다 null이면 None (skip)
        """
        # 최근 12주 week 서브쿼리
        recent_weeks = (
            self.db.query(JdAnalysis.week)
            .filter(JdAnalysis.parsed_at.isnot(None))
            .distinct()
            .order_by(desc(JdAnalysis.week))
            .limit(12)
            .subquery()
        )

        # 가장 빈도 높은 segment_id 조회
        row = (
            self.db.query(
                JdAnalysis.segment_id,
                func.count().label("cnt"),
            )
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
                JdAnalysis.week.in_(self.db.query(recent_weeks)),
            )
            .group_by(JdAnalysis.segment_id)
            .order_by(desc("cnt"))
            .first()
        )

        if row and row.segment_id:
            return row.segment_id

        # fallback: Company.segment_id
        company = self.db.query(Company.segment_id).filter(Company.id == company_id).first()
        if company and company.segment_id:
            return company.segment_id

        return None

    # ------------------------------------------------------------------ #
    #  Tech DNA
    # ------------------------------------------------------------------ #

    def _compute_tech_dna(self, company_id: uuid.UUID) -> dict:
        """Tech DNA 계산 — Shannon diversity index + top techs

        tech_stacks = DISTINCT(jd_analyses.tech_stacks) for company
        tech_diversity_index = -SUM(p_i * ln(p_i))  # Shannon entropy
        Guard: < 2 unique techs → diversity_index = 0
        """
        analyses = (
            self.db.query(JdAnalysis.tech_stacks)
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
                JdAnalysis.tech_stacks.isnot(None),
            )
            .all()
        )

        # 전체 기술 스택 빈도 계산
        tech_counter: Counter[str] = Counter()
        for row in analyses:
            if row.tech_stacks:
                tech_counter.update(row.tech_stacks)

        unique_count = len(tech_counter)
        total_mentions = sum(tech_counter.values())

        # Shannon entropy 계산 (unique tech < 2이면 0)
        if unique_count < 2 or total_mentions == 0:
            diversity_index = 0.0
        else:
            diversity_index = 0.0
            for count in tech_counter.values():
                p_i = count / total_mentions
                diversity_index -= p_i * math.log(p_i)

        # 상위 10개 기술
        top_techs = [
            {"name": name, "count": cnt}
            for name, cnt in tech_counter.most_common(10)
        ]

        return {
            "tech_stack_count": unique_count,
            "tech_diversity_index": round(diversity_index, 2),
            "top_techs": top_techs,
        }

    # ------------------------------------------------------------------ #
    #  Hiring DNA
    # ------------------------------------------------------------------ #

    def _compute_hiring_dna(self, company_id: uuid.UUID) -> dict:
        """Hiring DNA 계산 — growth velocity + role distribution

        growth_velocity: linear regression slope of weekly posting counts (last 4 weeks)
        If < 4 weeks of data → growth_velocity = None, growth_label = "데이터 부족"
        """
        # 최근 12주 주간 공고 수 (JdAnalysis 기준)
        weekly_counts = (
            self.db.query(
                JdAnalysis.week,
                func.count().label("cnt"),
            )
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
            )
            .group_by(JdAnalysis.week)
            .order_by(JdAnalysis.week)
            .all()
        )

        # 전체 공고 수
        total_postings = sum(r.cnt for r in weekly_counts) if weekly_counts else 0

        # growth velocity — 마지막 4주 데이터에 대한 선형 회귀
        growth_velocity = None
        if len(weekly_counts) >= 4:
            last4 = weekly_counts[-4:]
            n = 4
            xs = list(range(n))  # [0, 1, 2, 3]
            ys = [r.cnt for r in last4]
            sum_x = sum(xs)
            sum_y = sum(ys)
            sum_xy = sum(x * y for x, y in zip(xs, ys))
            sum_x2 = sum(x * x for x in xs)
            denom = n * sum_x2 - sum_x * sum_x
            if denom != 0:
                growth_velocity = round((n * sum_xy - sum_x * sum_y) / denom, 4)

        # 경력 수준 분포
        role_rows = (
            self.db.query(JdAnalysis.role_level, func.count().label("cnt"))
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
                JdAnalysis.role_level.isnot(None),
            )
            .group_by(JdAnalysis.role_level)
            .all()
        )
        role_level_dist = {r.role_level: r.cnt for r in role_rows}

        # 세그먼트 다양성
        seg_count = (
            self.db.query(func.count(distinct(JdAnalysis.segment_id)))
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
            )
            .scalar()
        ) or 0

        return {
            "total_postings": total_postings,
            "growth_velocity": growth_velocity,
            "role_level_dist": role_level_dist,
            "segment_breadth": seg_count,
        }

    # ------------------------------------------------------------------ #
    #  Compensation DNA
    # ------------------------------------------------------------------ #

    def _compute_compensation_dna(self, company_id: uuid.UUID) -> dict:
        """Compensation DNA 계산 — salary + equity + benefits

        salary_avg = AVG((salary_min + salary_max) / 2) where not null
        has_equity_ratio = COUNT(has_equity=true) / total
        position_label thresholds: >= 75 → "상위 25%", >= 40 → "평균 수준", < 40 → "하위 40%"
        """
        analyses = (
            self.db.query(JdAnalysis)
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
            )
            .all()
        )

        if not analyses:
            return {
                "salary_avg": None,
                "salary_min": None,
                "salary_max": None,
                "has_equity_ratio": 0.0,
                "benefits_count": 0,
                "top_benefits": [],
            }

        # 연봉 집계
        salary_mids: list[float] = []
        all_mins: list[int] = []
        all_maxs: list[int] = []
        for a in analyses:
            if a.salary_min is not None and a.salary_max is not None:
                salary_mids.append((a.salary_min + a.salary_max) / 2)
                all_mins.append(a.salary_min)
                all_maxs.append(a.salary_max)
            elif a.salary_min is not None:
                salary_mids.append(float(a.salary_min))
                all_mins.append(a.salary_min)
            elif a.salary_max is not None:
                salary_mids.append(float(a.salary_max))
                all_maxs.append(a.salary_max)

        salary_avg = round(sum(salary_mids) / len(salary_mids)) if salary_mids else None
        salary_min_val = min(all_mins) if all_mins else None
        salary_max_val = max(all_maxs) if all_maxs else None

        # equity / benefits — parsed_data JSONB에서 추출
        total = len(analyses)
        equity_count = 0
        benefits_counter: Counter[str] = Counter()

        for a in analyses:
            pd = a.parsed_data or {}
            comp_data = pd.get("compensation", {})
            if comp_data.get("has_equity"):
                equity_count += 1
            benefits = comp_data.get("benefits", [])
            if isinstance(benefits, list):
                benefits_counter.update(benefits)

        has_equity_ratio = round(equity_count / total, 2) if total > 0 else 0.0
        benefits_count = len(benefits_counter)
        # 스키마가 list[str]을 기대하므로 이름만 반환
        top_benefits = [name for name, _ in benefits_counter.most_common(10)]

        return {
            "salary_avg": salary_avg,
            "salary_min": salary_min_val,
            "salary_max": salary_max_val,
            "has_equity_ratio": has_equity_ratio,
            "benefits_count": benefits_count,
            "top_benefits": top_benefits,
        }

    # ------------------------------------------------------------------ #
    #  Culture Signals
    # ------------------------------------------------------------------ #

    def _compute_culture_signals(self, company_id: uuid.UUID) -> dict:
        """Culture Signals 계산

        growth_stage = MODE(parsed_data.org_signals.growth_stage)
        new_position_ratio = COUNT(is_new_position=true) / total
        culture_score = benefits_count_normalized * 0.4 + new_position_ratio * 0.3 + has_equity_ratio * 0.3
        """
        analyses = (
            self.db.query(JdAnalysis.parsed_data)
            .filter(
                JdAnalysis.company_id == company_id,
                JdAnalysis.parsed_at.isnot(None),
            )
            .all()
        )

        if not analyses:
            return {
                "team_size_signals": [],
                "growth_stage": None,
                "new_position_ratio": 0.0,
                "culture_score": 0.0,
            }

        total = len(analyses)
        growth_stages: list[str] = []
        team_sizes: list[str] = []
        new_position_count = 0

        for row in analyses:
            pd = row.parsed_data or {}
            org = pd.get("org_signals", {})
            if isinstance(org, dict):
                gs = org.get("growth_stage")
                if gs:
                    growth_stages.append(gs)
                ts = org.get("team_size")
                if ts:
                    team_sizes.append(str(ts))
                if org.get("is_new_position"):
                    new_position_count += 1

        # MODE of growth_stage
        growth_stage = None
        if growth_stages:
            stage_counter = Counter(growth_stages)
            growth_stage = stage_counter.most_common(1)[0][0]

        new_position_ratio = round(new_position_count / total, 2) if total > 0 else 0.0

        # team_size_signals — 상위 5개
        ts_counter = Counter(team_sizes)
        team_size_signals = [
            {"size": s, "count": c}
            for s, c in ts_counter.most_common(5)
        ]

        return {
            "team_size_signals": team_size_signals,
            "growth_stage": growth_stage,
            "new_position_ratio": new_position_ratio,
            # culture_score는 compute_dna_snapshot에서 최종 계산
        }

    # ------------------------------------------------------------------ #
    #  DNA 스냅샷 계산 + Upsert
    # ------------------------------------------------------------------ #

    def compute_dna_snapshot(self, company_id: uuid.UUID, week: str) -> dict | None:
        """단일 기업의 DNA 스냅샷 계산 — jd_analyses 기반
        Uses INSERT ... ON CONFLICT (company_id, week) DO UPDATE
        Returns the computed snapshot dict or None if company should be skipped
        """
        segment_id = self.resolve_segment_id(company_id)
        if not segment_id:
            return None

        tech = self._compute_tech_dna(company_id)
        hiring = self._compute_hiring_dna(company_id)
        comp = self._compute_compensation_dna(company_id)
        culture = self._compute_culture_signals(company_id)

        # culture_score 계산
        # benefits_count를 0~1로 정규화 (10개 이상이면 1.0)
        benefits_normalized = min(comp["benefits_count"] / 10.0, 1.0) if comp["benefits_count"] > 0 else 0.0
        culture_score = round(
            benefits_normalized * 0.4
            + culture["new_position_ratio"] * 0.3
            + comp["has_equity_ratio"] * 0.3,
            2,
        )

        # overall_dna_score (가중 합산) — 백분위 기반 점수는 아직 없으므로 raw 지표 사용
        # tech_diversity * 0.35 + hiring_intensity * 0.30 + salary_position * 0.20 + culture * 0.15
        # salary_position이 None이면 50을 neutral default로 사용
        # 참고: 백분위 점수는 compute_segment_percentiles에서 나중에 업데이트됨
        overall_dna_score = 0.0  # 백분위 계산 후 최종 업데이트

        snapshot_data = {
            "company_id": company_id,
            "segment_id": segment_id,
            "week": week,
            # Tech DNA
            "tech_stack_count": tech["tech_stack_count"],
            "tech_diversity_index": tech["tech_diversity_index"],
            "top_techs": tech["top_techs"],
            "tech_diversity_score": 0,  # 백분위 계산 후 업데이트
            # Hiring DNA
            "total_postings": hiring["total_postings"],
            "growth_velocity": hiring["growth_velocity"],
            "role_level_dist": hiring["role_level_dist"],
            "segment_breadth": hiring["segment_breadth"],
            "hiring_intensity_score": 0,  # 백분위 계산 후 업데이트
            # Compensation DNA
            "salary_avg": comp["salary_avg"],
            "salary_min": comp["salary_min"],
            "salary_max": comp["salary_max"],
            "salary_position_pct": None,  # 백분위 계산 후 업데이트
            "has_equity_ratio": comp["has_equity_ratio"],
            "benefits_count": comp["benefits_count"],
            "top_benefits": comp["top_benefits"],
            # Culture Signals
            "team_size_signals": culture["team_size_signals"],
            "growth_stage": culture["growth_stage"],
            "new_position_ratio": culture["new_position_ratio"],
            "culture_score": culture_score,
            # Overall
            "overall_dna_score": overall_dna_score,
        }

        # PostgreSQL UPSERT
        stmt = pg_insert(CompanyDnaSnapshot).values(**snapshot_data)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_dna_company_week",
            set_={
                k: stmt.excluded[k]
                for k in snapshot_data
                if k not in ("company_id", "week")
            },
        )
        self.db.execute(stmt)
        self.db.flush()

        return snapshot_data

    # ------------------------------------------------------------------ #
    #  세그먼트 내 백분위 계산
    # ------------------------------------------------------------------ #

    def compute_segment_percentiles(self, segment_id: str, week: str) -> None:
        """세그먼트 내 백분위 일괄 계산

        IMPORTANT: This must run AFTER all raw snapshots are computed.
        Updates: tech_diversity_score, hiring_intensity_score, salary_position_pct

        For each metric, rank companies within the segment and convert to percentile (0-100).
        """
        snapshots = (
            self.db.query(CompanyDnaSnapshot)
            .filter(
                CompanyDnaSnapshot.segment_id == segment_id,
                CompanyDnaSnapshot.week == week,
            )
            .all()
        )

        total = len(snapshots)
        if total == 0:
            return

        def _rank_to_percentile(sorted_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
            """순위 → 백분위 변환. 단일 기업이면 50 반환."""
            n = len(sorted_ids)
            if n <= 1:
                return {cid: 50.0 for cid in sorted_ids}
            return {
                cid: round((rank / (n - 1)) * 100, 2)
                for rank, cid in enumerate(sorted_ids)
            }

        # tech_diversity_index 기준 정렬 (오름차순 → 높을수록 높은 백분위)
        by_tech = sorted(snapshots, key=lambda s: float(s.tech_diversity_index or 0))
        tech_pcts = _rank_to_percentile([s.company_id for s in by_tech])

        # total_postings 기준 (hiring intensity)
        by_hiring = sorted(snapshots, key=lambda s: s.total_postings or 0)
        hiring_pcts = _rank_to_percentile([s.company_id for s in by_hiring])

        # salary_avg 기준 (None은 제외하고 별도 처리)
        with_salary = [s for s in snapshots if s.salary_avg is not None]
        salary_pcts: dict[uuid.UUID, float | None] = {}
        if with_salary:
            by_salary = sorted(with_salary, key=lambda s: s.salary_avg or 0)
            salary_pcts = _rank_to_percentile([s.company_id for s in by_salary])

        # 각 스냅샷 업데이트
        for s in snapshots:
            s.tech_diversity_score = tech_pcts.get(s.company_id, 50.0)
            s.hiring_intensity_score = hiring_pcts.get(s.company_id, 50.0)
            s.salary_position_pct = salary_pcts.get(s.company_id)

            # overall_dna_score 계산 (가중 합산)
            tech_score = float(s.tech_diversity_score or 0)
            hiring_score = float(s.hiring_intensity_score or 0)
            salary_score = float(s.salary_position_pct) if s.salary_position_pct is not None else 50.0
            culture = float(s.culture_score or 0) * 100  # 0~1 → 0~100 스케일

            s.overall_dna_score = round(
                tech_score * 0.35
                + hiring_score * 0.30
                + salary_score * 0.20
                + culture * 0.15,
                2,
            )

        self.db.flush()

    # ------------------------------------------------------------------ #
    #  전체 갱신
    # ------------------------------------------------------------------ #

    def refresh_all(self, week: str) -> dict:
        """전체 기업 DNA 일괄 갱신 — 스케줄러에서 호출

        Order of operations:
        1. Get all company_ids that have jd_analyses
        2. Compute raw DNA snapshot for each company
        3. THEN compute segment percentiles (must be after all raw snapshots)
        4. THEN update overall_dna_score with percentile-based values

        Uses ON CONFLICT DO UPDATE for idempotency.
        Returns stats dict {total_companies, computed, skipped, errors}
        """
        # 1. JD 분석이 존재하는 모든 기업 조회
        company_rows = (
            self.db.query(distinct(JdAnalysis.company_id))
            .filter(
                JdAnalysis.parsed_at.isnot(None),
                JdAnalysis.company_id.isnot(None),
            )
            .all()
        )
        company_ids = [r[0] for row in company_rows for r in [row]]

        stats = {"total_companies": len(company_ids), "computed": 0, "skipped": 0, "errors": 0}
        computed_segments: set[str] = set()

        # 2. 각 기업별 raw 스냅샷 계산
        for cid in company_ids:
            try:
                result = self.compute_dna_snapshot(cid, week)
                if result:
                    stats["computed"] += 1
                    computed_segments.add(result["segment_id"])
                else:
                    stats["skipped"] += 1
            except Exception:
                logger.exception("DNA snapshot 계산 실패: company_id=%s", cid)
                stats["errors"] += 1

        # 3. 세그먼트별 백분위 계산 (모든 raw 스냅샷 이후)
        for seg_id in computed_segments:
            try:
                self.compute_segment_percentiles(seg_id, week)
            except Exception:
                logger.exception("백분위 계산 실패: segment_id=%s", seg_id)
                stats["errors"] += 1

        self.db.commit()
        return stats

    # ------------------------------------------------------------------ #
    #  조회 API
    # ------------------------------------------------------------------ #

    def get_company_dna(self, company_id: str) -> dict | None:
        """최신 DNA 조회 (캐시 테이블에서)

        Returns the latest week's snapshot for the given company.
        Returns None if no snapshot exists.
        Format the response for API consumption.
        """
        try:
            cid = uuid.UUID(company_id)
        except ValueError:
            return None

        snapshot = (
            self.db.query(CompanyDnaSnapshot)
            .filter(CompanyDnaSnapshot.company_id == cid)
            .order_by(desc(CompanyDnaSnapshot.week))
            .first()
        )

        if not snapshot:
            return None

        # growth_label 결정
        gv = float(snapshot.growth_velocity) if snapshot.growth_velocity is not None else None
        if gv is None:
            growth_label = "데이터 부족"
        elif gv > 2.0:
            growth_label = "급성장"
        elif gv > 0.5:
            growth_label = "성장"
        elif gv >= -0.5:
            growth_label = "안정"
        else:
            growth_label = "감소"

        # position_label 결정
        sp = float(snapshot.salary_position_pct) if snapshot.salary_position_pct is not None else None
        if sp is None:
            position_label = None
        elif sp >= 75:
            position_label = "상위 25%"
        elif sp >= 40:
            position_label = "평균 수준"
        else:
            position_label = "하위 40%"

        # 회사 이름 조회
        company = self.db.query(Company).filter(Company.id == cid).first()
        company_name = company.name if company else company_id

        return {
            "company_id": company_id,
            "company_name": company_name,
            "segment_id": snapshot.segment_id,
            "week": snapshot.week,
            "tech": {
                "stack_count": snapshot.tech_stack_count,
                "diversity_index": float(snapshot.tech_diversity_index),
                "diversity_score": float(snapshot.tech_diversity_score),
                "top_techs": snapshot.top_techs,
            },
            "hiring": {
                "total_postings": snapshot.total_postings,
                "growth_velocity": gv,
                "growth_label": growth_label,
                "role_distribution": snapshot.role_level_dist or {},
                "segment_breadth": snapshot.segment_breadth,
                "intensity_score": float(snapshot.hiring_intensity_score),
            },
            "compensation": {
                "salary_avg": snapshot.salary_avg,
                "salary_min": snapshot.salary_min,
                "salary_max": snapshot.salary_max,
                "position_percentile": sp,
                "position_label": position_label or "데이터 없음",
                "equity_ratio": float(snapshot.has_equity_ratio),
                "benefits_count": snapshot.benefits_count,
                "top_benefits": snapshot.top_benefits or [],
            },
            "culture": {
                "team_size_patterns": snapshot.team_size_signals or [],
                "growth_stage": snapshot.growth_stage,
                "new_position_ratio": float(snapshot.new_position_ratio),
                "culture_score": float(snapshot.culture_score),
            },
            "overall_score": float(snapshot.overall_dna_score),
        }

    def get_segment_benchmarks(self, segment_id: str) -> dict | None:
        """세그먼트 평균 DNA (비교 기준선)

        Average all DNA scores for companies in this segment for the latest week.
        Returns segment average stats.
        """
        # 최신 week 조회
        latest_week = (
            self.db.query(func.max(CompanyDnaSnapshot.week))
            .filter(CompanyDnaSnapshot.segment_id == segment_id)
            .scalar()
        )

        if not latest_week:
            return None

        snapshots = (
            self.db.query(CompanyDnaSnapshot)
            .filter(
                CompanyDnaSnapshot.segment_id == segment_id,
                CompanyDnaSnapshot.week == latest_week,
            )
            .all()
        )

        if not snapshots:
            return None

        n = len(snapshots)

        def _avg(values: list) -> float | None:
            filtered = [v for v in values if v is not None]
            return round(sum(filtered) / len(filtered), 2) if filtered else None

        # 세그먼트 이름 조회
        from app.constants.segments import SEGMENTS
        seg_info = next((s for s in SEGMENTS if s["id"] == segment_id), None)
        segment_name = seg_info["name_ko"] if seg_info else segment_id

        avg_salary_val = _avg([s.salary_avg for s in snapshots])

        return {
            "segment_id": segment_id,
            "segment_name": segment_name,
            "avg_tech_score": _avg([float(s.tech_diversity_score) for s in snapshots]) or 0.0,
            "avg_hiring_score": _avg([float(s.hiring_intensity_score) for s in snapshots]) or 0.0,
            "avg_salary": int(avg_salary_val) if avg_salary_val is not None else None,
            "avg_culture_score": _avg([float(s.culture_score) for s in snapshots]) or 0.0,
            "company_count": n,
        }

    # ------------------------------------------------------------------ #
    #  Backfill (cold start)
    # ------------------------------------------------------------------ #

    def backfill_all_weeks(self) -> dict:
        """과거 모든 주차에 대해 DNA 스냅샷 일괄 생성 (cold start 대응)

        1. Get DISTINCT(week) from jd_analyses
        2. For each week: refresh_all(week)
        Returns stats.
        """
        weeks = (
            self.db.query(distinct(JdAnalysis.week))
            .filter(JdAnalysis.parsed_at.isnot(None))
            .order_by(JdAnalysis.week)
            .all()
        )
        week_list = [r[0] for r in weeks]

        total_stats = {"weeks_processed": 0, "total_computed": 0, "total_skipped": 0, "total_errors": 0}

        for w in week_list:
            logger.info("Backfilling DNA snapshots for week=%s", w)
            stats = self.refresh_all(w)
            total_stats["weeks_processed"] += 1
            total_stats["total_computed"] += stats["computed"]
            total_stats["total_skipped"] += stats["skipped"]
            total_stats["total_errors"] += stats["errors"]

        return total_stats
