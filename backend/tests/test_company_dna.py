"""Company DNA 서비스 + API 테스트"""
import math
import uuid
from unittest.mock import patch, MagicMock

import pytest

from app.services.company_dna_service import CompanyDnaService


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _make_service():
    db = MagicMock()
    return CompanyDnaService(db), db


# CompanyDnaResponse(**data) 호출에 맞는 dict (스키마 필드명 기준)
def _company_dna_dict(company_id: str) -> dict:
    return {
        "company_id": company_id,
        "company_name": "토스",
        "segment_id": "dev_server",
        "week": "2026-W01",
        "overall_score": 72.5,
        "tech": {
            "stack_count": 5,
            "diversity_index": 1.5,
            "diversity_score": 70.0,
            "top_techs": [],
        },
        "hiring": {
            "total_postings": 20,
            "growth_velocity": 1.5,
            "growth_label": "성장",
            "intensity_score": 60.0,
            "role_distribution": {"senior": 10},
            "segment_breadth": 2,
        },
        "compensation": {
            "salary_avg": 6000,
            "salary_min": 4000,
            "salary_max": 9000,
            "position_percentile": 80.0,
            "position_label": "상위 25%",
            "equity_ratio": 0.6,
            "benefits_count": 8,
            "top_benefits": [],
        },
        "culture": {
            "growth_stage": "scale-up",
            "new_position_ratio": 0.4,
            "team_size_patterns": [],
            "culture_score": 55.0,
        },
    }


# SegmentBenchmarkResponse(**data) 호출에 맞는 dict
def _segment_benchmark_dict() -> dict:
    return {
        "segment_id": "dev_server",
        "segment_name": "서버/백엔드",
        "avg_tech_score": 55.0,
        "avg_hiring_score": 48.0,
        "avg_salary": 5500,
        "avg_culture_score": 0.5,
        "company_count": 15,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Shannon Diversity
# ─────────────────────────────────────────────────────────────────────────────

class TestShannonDiversity:
    """_compute_tech_dna — diversity_index 계산 검증"""

    def _run(self, tech_lists):
        service, db = _make_service()
        rows = [MagicMock(tech_stacks=tl) for tl in tech_lists]
        db.query.return_value.filter.return_value.all.return_value = rows
        return service._compute_tech_dna(uuid.uuid4())

    def test_single_tech_diversity_is_zero(self):
        """단일 기술만 존재 → diversity_index = 0 (unique < 2)"""
        result = self._run([["Python"], ["Python"], ["Python"]])
        assert result["tech_diversity_index"] == 0.0
        assert result["tech_stack_count"] == 1

    def test_uniform_distribution_max_entropy(self):
        """4개 기술이 동일 빈도 → entropy ≈ ln(4) ≈ 1.39"""
        result = self._run([["A"], ["B"], ["C"], ["D"]])
        expected = round(-4 * (0.25 * math.log(0.25)), 2)
        assert abs(result["tech_diversity_index"] - expected) <= 0.01
        assert result["tech_stack_count"] == 4

    def test_skewed_distribution_low_entropy(self):
        """한 기술 압도적 → 낮은 엔트로피"""
        result = self._run([["Python"]] * 9 + [["Go"]])
        assert result["tech_diversity_index"] < 0.5
        assert result["tech_stack_count"] == 2

    def test_empty_analyses(self):
        """데이터 없음 → 기본값"""
        result = self._run([])
        assert result["tech_stack_count"] == 0
        assert result["tech_diversity_index"] == 0.0
        assert result["top_techs"] == []


# ─────────────────────────────────────────────────────────────────────────────
# 2. Growth Velocity
# ─────────────────────────────────────────────────────────────────────────────

class TestGrowthVelocity:
    """_compute_hiring_dna — growth_velocity 선형회귀 검증"""

    def _run(self, weekly_counts):
        service, db = _make_service()

        rows = []
        for i, cnt in enumerate(weekly_counts):
            r = MagicMock()
            r.week = f"2026-W{i+1:02d}"
            r.cnt = cnt
            rows.append(r)

        call_idx = [0]

        def _q(*args, **kwargs):
            q = MagicMock()
            q.filter.return_value = q
            q.group_by.return_value = q
            q.order_by.return_value = q
            if call_idx[0] == 0:
                q.all.return_value = rows
            else:
                q.all.return_value = []
                q.scalar.return_value = 0
            call_idx[0] += 1
            return q

        service.db.query.side_effect = _q
        return service._compute_hiring_dna(uuid.uuid4())

    def test_increasing_trend(self):
        """증가 추세 → 양의 기울기"""
        result = self._run([1, 2, 3, 4])
        assert result["growth_velocity"] is not None
        assert result["growth_velocity"] > 0

    def test_decreasing_trend(self):
        """감소 추세 → 음의 기울기"""
        result = self._run([4, 3, 2, 1])
        assert result["growth_velocity"] is not None
        assert result["growth_velocity"] < 0

    def test_flat_trend(self):
        """동일한 수 → 기울기 = 0"""
        result = self._run([5, 5, 5, 5])
        assert result["growth_velocity"] == 0.0

    def test_insufficient_data(self):
        """3주 이하 데이터 → None"""
        result = self._run([10, 20, 30])
        assert result["growth_velocity"] is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Percentile Ranking
# ─────────────────────────────────────────────────────────────────────────────

class TestPercentileRanking:
    """compute_segment_percentiles — 백분위 계산 검증"""

    def test_three_companies_ranked(self):
        """3개 기업 → 백분위 0, 50, 100"""
        service, db = _make_service()

        cids = [uuid.uuid4() for _ in range(3)]
        snapshots = []
        for i, cid in enumerate(cids):
            s = MagicMock()
            s.company_id = cid
            s.tech_diversity_index = float(i)
            s.total_postings = i + 1
            s.salary_avg = (i + 1) * 1000
            s.salary_position_pct = None
            s.culture_score = 0.5
            snapshots.append(s)

        db.query.return_value.filter.return_value.all.return_value = snapshots
        service.compute_segment_percentiles("dev_server", "2026-W01")

        assert snapshots[0].tech_diversity_score == 0.0
        assert snapshots[1].tech_diversity_score == 50.0
        assert snapshots[2].tech_diversity_score == 100.0
        assert snapshots[0].hiring_intensity_score == 0.0
        assert snapshots[2].hiring_intensity_score == 100.0

    def test_single_company_gets_50(self):
        """기업 1개 → 모든 백분위 50"""
        service, db = _make_service()

        s = MagicMock()
        s.company_id = uuid.uuid4()
        s.tech_diversity_index = 1.5
        s.total_postings = 10
        s.salary_avg = 5000
        s.salary_position_pct = None
        s.culture_score = 0.5

        db.query.return_value.filter.return_value.all.return_value = [s]
        service.compute_segment_percentiles("dev_server", "2026-W01")

        assert s.tech_diversity_score == 50.0
        assert s.hiring_intensity_score == 50.0

    def test_no_snapshots_returns_early(self):
        """스냅샷 없음 → 조기 반환, 에러 없음"""
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        service.compute_segment_percentiles("dev_server", "2026-W01")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Segment Assignment
# ─────────────────────────────────────────────────────────────────────────────

class TestSegmentAssignment:
    """resolve_segment_id — 세그먼트 결정 규칙 검증"""

    def test_from_jd_analyses(self):
        """jd_analyses에서 가장 많은 segment_id 반환"""
        service, db = _make_service()

        row = MagicMock()
        row.segment_id = "dev_server"

        q = MagicMock()
        q.filter.return_value = q
        q.distinct.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.subquery.return_value = MagicMock()
        q.group_by.return_value = q
        q.first.return_value = row
        db.query.return_value = q

        result = service.resolve_segment_id(uuid.uuid4())
        assert result == "dev_server"

    def test_fallback_to_company_segment(self):
        """jd_analyses segment_id 없음 → Company.segment_id 사용"""
        service, db = _make_service()
        call_idx = [0]

        def _q(*args, **kwargs):
            q = MagicMock()
            q.filter.return_value = q
            q.distinct.return_value = q
            q.order_by.return_value = q
            q.limit.return_value = q
            q.subquery.return_value = MagicMock()
            q.group_by.return_value = q
            r = MagicMock()
            r.segment_id = None if call_idx[0] == 0 else "product"
            q.first.return_value = r
            call_idx[0] += 1
            return q

        db.query.side_effect = _q
        result = service.resolve_segment_id(uuid.uuid4())
        assert result == "product"

    def test_returns_none_when_both_null(self):
        """jd_analyses + Company 모두 null → None"""
        service, db = _make_service()

        def _q_null(*args, **kwargs):
            q = MagicMock()
            q.filter.return_value = q
            q.distinct.return_value = q
            q.order_by.return_value = q
            q.limit.return_value = q
            q.subquery.return_value = MagicMock()
            q.group_by.return_value = q
            r = MagicMock()
            r.segment_id = None
            q.first.return_value = r
            return q

        db.query.side_effect = _q_null
        result = service.resolve_segment_id(uuid.uuid4())
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# 5. Culture Score
# ─────────────────────────────────────────────────────────────────────────────

class TestCultureScore:
    """compute_dna_snapshot — culture_score 공식 검증"""

    def test_culture_score_formula(self):
        """culture_score = benefits_normalized*0.4 + new_pos_ratio*0.3 + equity_ratio*0.3"""
        service, db = _make_service()

        with patch.object(service, "resolve_segment_id", return_value="dev_server"), \
             patch.object(service, "_compute_tech_dna", return_value={
                 "tech_stack_count": 3, "tech_diversity_index": 1.2, "top_techs": [],
             }), \
             patch.object(service, "_compute_hiring_dna", return_value={
                 "total_postings": 10, "growth_velocity": 1.0,
                 "role_level_dist": {}, "segment_breadth": 1,
             }), \
             patch.object(service, "_compute_compensation_dna", return_value={
                 "salary_avg": 5000, "salary_min": 3000, "salary_max": 7000,
                 "has_equity_ratio": 0.5,
                 "benefits_count": 5,
                 "top_benefits": [],
             }), \
             patch.object(service, "_compute_culture_signals", return_value={
                 "team_size_signals": [], "growth_stage": "scale-up",
                 "new_position_ratio": 0.4,
             }):

            db.execute.return_value = MagicMock()
            db.flush.return_value = None
            result = service.compute_dna_snapshot(uuid.uuid4(), "2026-W01")

        # benefits_count=5 → normalized=0.5
        # 0.5*0.4 + 0.4*0.3 + 0.5*0.3 = 0.47
        assert result is not None
        assert result["culture_score"] == round(0.5 * 0.4 + 0.4 * 0.3 + 0.5 * 0.3, 2)

    def test_benefits_count_capped_at_1(self):
        """benefits_count >= 10 → normalized = 1.0"""
        service, db = _make_service()

        with patch.object(service, "resolve_segment_id", return_value="dev_server"), \
             patch.object(service, "_compute_tech_dna", return_value={
                 "tech_stack_count": 1, "tech_diversity_index": 0.0, "top_techs": [],
             }), \
             patch.object(service, "_compute_hiring_dna", return_value={
                 "total_postings": 5, "growth_velocity": None,
                 "role_level_dist": {}, "segment_breadth": 1,
             }), \
             patch.object(service, "_compute_compensation_dna", return_value={
                 "salary_avg": None, "salary_min": None, "salary_max": None,
                 "has_equity_ratio": 1.0,
                 "benefits_count": 15,
                 "top_benefits": [],
             }), \
             patch.object(service, "_compute_culture_signals", return_value={
                 "team_size_signals": [], "growth_stage": None,
                 "new_position_ratio": 1.0,
             }):

            db.execute.return_value = MagicMock()
            db.flush.return_value = None
            result = service.compute_dna_snapshot(uuid.uuid4(), "2026-W01")

        # 1.0*0.4 + 1.0*0.3 + 1.0*0.3 = 1.0
        assert result is not None
        assert result["culture_score"] == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Compensation DNA edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestCompensationDna:
    """_compute_compensation_dna — 연봉 집계 엣지 케이스"""

    def _run(self, analyses):
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = analyses
        return service._compute_compensation_dna(uuid.uuid4())

    def test_all_salary_null(self):
        """모든 salary null → salary 필드 null"""
        analyses = [MagicMock(salary_min=None, salary_max=None, parsed_data={}) for _ in range(3)]
        result = self._run(analyses)
        assert result["salary_avg"] is None
        assert result["salary_min"] is None
        assert result["salary_max"] is None

    def test_salary_only_min(self):
        """salary_min만 있을 때 avg = salary_min"""
        a = MagicMock()
        a.salary_min = 4000
        a.salary_max = None
        a.parsed_data = {}
        result = self._run([a])
        assert result["salary_avg"] == 4000

    def test_equity_ratio(self):
        """has_equity=True 2/4 → ratio = 0.5"""
        analyses = []
        for i in range(4):
            a = MagicMock()
            a.salary_min = None
            a.salary_max = None
            a.parsed_data = {"compensation": {"has_equity": i < 2, "benefits": []}}
            analyses.append(a)
        result = self._run(analyses)
        assert result["has_equity_ratio"] == 0.5

    def test_empty_analyses(self):
        """분석 없음 → 기본값"""
        result = self._run([])
        assert result["salary_avg"] is None
        assert result["has_equity_ratio"] == 0.0
        assert result["benefits_count"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 7. Culture Signals edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestCultureSignals:
    """_compute_culture_signals — org_signals 파싱 검증"""

    def _run(self, analyses):
        service, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = analyses
        return service._compute_culture_signals(uuid.uuid4())

    def test_missing_org_signals(self):
        """parsed_data에 org_signals 없음 → 기본값"""
        analyses = [
            MagicMock(parsed_data={"compensation": {}}),
            MagicMock(parsed_data={}),
        ]
        result = self._run(analyses)
        assert result["growth_stage"] is None
        assert result["new_position_ratio"] == 0.0
        assert result["team_size_signals"] == []

    def test_growth_stage_mode(self):
        """가장 빈도 높은 growth_stage 반환"""
        analyses = [
            MagicMock(parsed_data={"org_signals": {"growth_stage": "scale-up", "is_new_position": False}}),
            MagicMock(parsed_data={"org_signals": {"growth_stage": "scale-up", "is_new_position": True}}),
            MagicMock(parsed_data={"org_signals": {"growth_stage": "startup", "is_new_position": True}}),
        ]
        result = self._run(analyses)
        assert result["growth_stage"] == "scale-up"
        assert round(result["new_position_ratio"], 2) == round(2 / 3, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 8. API Integration Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanyDnaEndpoint:
    """GET /api/v1/dashboard/company-dna/{company_id}"""

    @patch("app.services.company_dna_service.CompanyDnaService.get_company_dna")
    def test_success(self, mock_get_dna, client, mock_pro_user):
        """PRO 사용자 + 유효한 기업 → 200"""
        company_id = str(uuid.uuid4())
        mock_get_dna.return_value = _company_dna_dict(company_id)

        response = client.get(f"/api/v1/dashboard/company-dna/{company_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["companyId"] == company_id
        assert data["data"]["overallScore"] == 72.5

    @patch("app.services.company_dna_service.CompanyDnaService.get_company_dna")
    def test_not_found(self, mock_get_dna, client, mock_pro_user):
        """존재하지 않는 기업 → 404"""
        mock_get_dna.return_value = None
        response = client.get(f"/api/v1/dashboard/company-dna/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_starter_forbidden(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.get(f"/api/v1/dashboard/company-dna/{uuid.uuid4()}")
        assert response.status_code == 403


class TestSegmentBenchmarkEndpoint:
    """GET /api/v1/dashboard/segment-benchmark/{segment_id}"""

    @patch("app.services.company_dna_service.CompanyDnaService.get_segment_benchmarks")
    def test_success(self, mock_get_benchmarks, client, mock_pro_user):
        """PRO 사용자 + 유효한 세그먼트 → 200"""
        mock_get_benchmarks.return_value = _segment_benchmark_dict()

        response = client.get("/api/v1/dashboard/segment-benchmark/dev_server")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["segmentId"] == "dev_server"
        assert data["data"]["companyCount"] == 15

    @patch("app.services.company_dna_service.CompanyDnaService.get_segment_benchmarks")
    def test_not_found(self, mock_get_benchmarks, client, mock_pro_user):
        """존재하지 않는 세그먼트 → 404"""
        mock_get_benchmarks.return_value = None
        response = client.get("/api/v1/dashboard/segment-benchmark/nonexistent")
        assert response.status_code == 404

    def test_starter_forbidden(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.get("/api/v1/dashboard/segment-benchmark/dev_server")
        assert response.status_code == 403


class TestBackfillDnaEndpoint:
    """POST /api/v1/admin/backfill-dna"""

    def test_non_admin_forbidden(self, client, mock_pro_user):
        """PRO 사용자 → 403"""
        response = client.post("/api/v1/admin/backfill-dna")
        assert response.status_code == 403

    @patch("app.services.company_dna_service.CompanyDnaService.backfill_all_weeks")
    def test_admin_success(self, mock_backfill, client, mock_admin):
        """SUPER_ADMIN → 200, 백필 결과 반환"""
        mock_backfill.return_value = {
            "weeks_processed": 5,
            "total_computed": 80,
            "total_skipped": 10,
            "total_errors": 0,
        }
        response = client.post("/api/v1/admin/backfill-dna")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # ApiResponse[dict] — dict는 camelCase 변환 안 됨
        assert data["data"]["weeks_processed"] == 5
        assert data["data"]["total_computed"] == 80
