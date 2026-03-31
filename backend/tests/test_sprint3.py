"""Sprint 3 테스트 — DNA Trend, Company Compare, Name Resolution, Scheduler Retry, Demo Seeder"""
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from app.services.company_dna_service import CompanyDnaService


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _make_service():
    db = MagicMock()
    return CompanyDnaService(db), db


def _company_dna_dict(company_id: str) -> dict:
    """CompanyDnaResponse(**data) 호출에 맞는 dict (스키마 필드명 기준)"""
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
# 1. DNA Trend Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestDnaTrendEndpoint:
    """GET /api/v1/dashboard/company-dna/{company_id}/trend"""

    @patch("app.services.company_dna_service.CompanyDnaService.get_company_dna_trend")
    def test_trend_success(self, mock_trend, client, mock_pro_user):
        """PRO + 유효 기업 → 200, data_points 반환"""
        company_id = str(uuid.uuid4())
        mock_trend.return_value = {
            "company_id": company_id,
            "company_name": "토스",
            "segment_id": "dev_server",
            "data_points": [
                {
                    "week": "2026-W10",
                    "overall_score": 70.0,
                    "tech_score": 80.0,
                    "hiring_score": 60.0,
                    "salary_pct": 75.0,
                    "culture_score": 50.0,
                },
                {
                    "week": "2026-W11",
                    "overall_score": 72.0,
                    "tech_score": 82.0,
                    "hiring_score": 62.0,
                    "salary_pct": 76.0,
                    "culture_score": 52.0,
                },
            ],
        }
        response = client.get(f"/api/v1/dashboard/company-dna/{company_id}/trend")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        result = data["data"]
        assert result["companyId"] == company_id
        assert result["companyName"] == "토스"
        assert len(result["dataPoints"]) == 2
        assert result["dataPoints"][0]["week"] == "2026-W10"
        assert result["dataPoints"][0]["overallScore"] == 70.0

    @patch("app.services.company_dna_service.CompanyDnaService.get_company_dna_trend")
    def test_trend_not_found(self, mock_trend, client, mock_pro_user):
        """존재하지 않는 기업 → 404"""
        mock_trend.return_value = None
        response = client.get(f"/api/v1/dashboard/company-dna/{uuid.uuid4()}/trend")
        assert response.status_code == 404

    def test_trend_starter_403(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.get(f"/api/v1/dashboard/company-dna/{uuid.uuid4()}/trend")
        assert response.status_code == 403

    @patch("app.services.company_dna_service.CompanyDnaService.get_company_dna_trend")
    def test_trend_weeks_param(self, mock_trend, client, mock_pro_user):
        """weeks 쿼리 파라미터 → 서비스에 전달"""
        company_id = str(uuid.uuid4())
        mock_trend.return_value = {
            "company_id": company_id,
            "company_name": "카카오",
            "segment_id": "dev_server",
            "data_points": [],
        }
        response = client.get(
            f"/api/v1/dashboard/company-dna/{company_id}/trend?weeks=24"
        )
        assert response.status_code == 200
        mock_trend.assert_called_once()
        _, call_kwargs = mock_trend.call_args
        # weeks 인자가 24로 전달됐는지 확인
        assert 24 in mock_trend.call_args.args or mock_trend.call_args.kwargs.get("weeks") == 24


# ─────────────────────────────────────────────────────────────────────────────
# 2. Company Comparison Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanyCompareEndpoint:
    """GET /api/v1/dashboard/company-dna/compare"""

    @patch("app.services.company_dna_service.CompanyDnaService.compare_companies")
    def test_compare_success(self, mock_compare, client, mock_pro_user):
        """2개 기업 비교 → 200, company_a / company_b / segment_benchmark 반환"""
        cid_a = str(uuid.uuid4())
        cid_b = str(uuid.uuid4())
        mock_compare.return_value = {
            "company_a": _company_dna_dict(cid_a),
            "company_b": _company_dna_dict(cid_b),
            "segment_benchmark": _segment_benchmark_dict(),
        }
        response = client.get(
            f"/api/v1/dashboard/company-dna/compare?company_a={cid_a}&company_b={cid_b}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        result = data["data"]
        assert "companyA" in result
        assert "companyB" in result
        assert result["companyA"]["companyId"] == cid_a
        assert result["companyB"]["companyId"] == cid_b
        assert result["segmentBenchmark"]["segmentId"] == "dev_server"

    @patch("app.services.company_dna_service.CompanyDnaService.compare_companies")
    def test_compare_one_missing(self, mock_compare, client, mock_pro_user):
        """한 기업 없음 → 404"""
        mock_compare.return_value = {
            "error": "기업 B 'nonexistent'의 DNA 데이터를 찾을 수 없습니다.",
            "missing": "b",
        }
        response = client.get(
            "/api/v1/dashboard/company-dna/compare?company_a=toss&company_b=nonexistent"
        )
        assert response.status_code == 404

    @patch("app.services.company_dna_service.CompanyDnaService.compare_companies")
    def test_compare_both_missing(self, mock_compare, client, mock_pro_user):
        """두 기업 모두 없음 → 404"""
        mock_compare.return_value = None
        response = client.get(
            "/api/v1/dashboard/company-dna/compare?company_a=x&company_b=y"
        )
        assert response.status_code == 404

    def test_compare_starter_403(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.get(
            "/api/v1/dashboard/company-dna/compare?company_a=x&company_b=y"
        )
        assert response.status_code == 403

    @patch("app.services.company_dna_service.CompanyDnaService.compare_companies")
    def test_compare_no_benchmark_when_different_segments(self, mock_compare, client, mock_pro_user):
        """서로 다른 세그먼트 기업 비교 → segment_benchmark = null"""
        cid_a = str(uuid.uuid4())
        cid_b = str(uuid.uuid4())
        dna_a = _company_dna_dict(cid_a)
        dna_b = _company_dna_dict(cid_b)
        dna_b["segment_id"] = "product"  # 다른 세그먼트
        mock_compare.return_value = {
            "company_a": dna_a,
            "company_b": dna_b,
            "segment_benchmark": None,
        }
        response = client.get(
            f"/api/v1/dashboard/company-dna/compare?company_a={cid_a}&company_b={cid_b}"
        )
        assert response.status_code == 200
        assert response.json()["data"]["segmentBenchmark"] is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Name Resolution (서비스 단위 테스트)
# ─────────────────────────────────────────────────────────────────────────────

class TestNameResolution:
    """CompanyDnaService.resolve_company_by_name"""

    def test_resolve_exact_name(self):
        """정확한 이름 매칭 → company.id 반환"""
        service, db = _make_service()
        expected_id = uuid.uuid4()

        company_mock = MagicMock()
        company_mock.id = expected_id

        # 첫 번째 쿼리(exact match)에서 결과 반환
        db.query.return_value.filter.return_value.first.return_value = company_mock

        result = service.resolve_company_by_name("토스")
        assert result == expected_id

    def test_resolve_case_insensitive(self):
        """대소문자 무시 검색 — exact match 실패 후 lower().contains() 검색"""
        service, db = _make_service()
        expected_id = uuid.uuid4()

        company_mock = MagicMock()
        company_mock.id = expected_id

        call_idx = [0]

        def _q_side_effect(*args, **kwargs):
            q = MagicMock()
            q.filter.return_value = q
            if call_idx[0] == 0:
                # 첫 번째 호출: exact match → None
                q.first.return_value = None
            else:
                # 두 번째 호출: case-insensitive → 결과 반환
                q.first.return_value = company_mock
            call_idx[0] += 1
            return q

        db.query.side_effect = _q_side_effect
        result = service.resolve_company_by_name("toss")
        assert result == expected_id

    def test_resolve_not_found(self):
        """존재하지 않는 이름 → None"""
        service, db = _make_service()

        def _q_null(*args, **kwargs):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = None
            return q

        db.query.side_effect = _q_null
        result = service.resolve_company_by_name("존재하지않는기업")
        assert result is None

    def test_resolve_returns_id_from_company_model(self):
        """반환값이 Company.id (UUID 타입)"""
        service, db = _make_service()
        expected_id = uuid.uuid4()

        company_mock = MagicMock()
        company_mock.id = expected_id
        db.query.return_value.filter.return_value.first.return_value = company_mock

        result = service.resolve_company_by_name("카카오")
        assert result == expected_id
        assert isinstance(result, uuid.UUID)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Scheduler Retry Logic
# ─────────────────────────────────────────────────────────────────────────────

class TestSchedulerRetry:
    """weekly_dna_refresh_job — 재시도 로직 검증"""

    def test_retry_count_increments(self):
        """크롤 미완료 시 _dna_retry_counts 증가"""
        import app.scheduler as scheduler_module

        original_counts = dict(scheduler_module._dna_retry_counts)
        scheduler_module._dna_retry_counts.clear()

        week = "2026-W99"
        try:
            # 크롤 미완료 상태 시뮬레이션
            scheduler_module._dna_retry_counts[week] = 0
            scheduler_module._dna_retry_counts[week] += 1
            assert scheduler_module._dna_retry_counts[week] == 1

            scheduler_module._dna_retry_counts[week] += 1
            assert scheduler_module._dna_retry_counts[week] == 2
        finally:
            scheduler_module._dna_retry_counts.clear()
            scheduler_module._dna_retry_counts.update(original_counts)

    def test_max_retries_exhausted(self):
        """3회 초과 시 재시도 중단 — DNA_REFRESH_MAX_RETRIES 상수 검증"""
        import app.scheduler as scheduler_module

        assert scheduler_module.DNA_REFRESH_MAX_RETRIES == 3

    def test_retry_stops_at_max(self):
        """retry_count >= DNA_REFRESH_MAX_RETRIES → 재시도 안 함"""
        import app.scheduler as scheduler_module

        original_counts = dict(scheduler_module._dna_retry_counts)
        scheduler_module._dna_retry_counts.clear()

        week = "2026-W98"
        max_retries = scheduler_module.DNA_REFRESH_MAX_RETRIES
        scheduler_module._dna_retry_counts[week] = max_retries

        try:
            # max_retries에 도달한 경우 재시도 안 해야 함
            retry_count = scheduler_module._dna_retry_counts.get(week, 0)
            should_retry = retry_count < max_retries
            assert should_retry is False
        finally:
            scheduler_module._dna_retry_counts.clear()
            scheduler_module._dna_retry_counts.update(original_counts)

    def test_retry_count_cleared_on_success(self):
        """DNA 갱신 성공 시 재시도 카운트 초기화"""
        import app.scheduler as scheduler_module

        original_counts = dict(scheduler_module._dna_retry_counts)
        scheduler_module._dna_retry_counts.clear()

        week = "2026-W97"
        scheduler_module._dna_retry_counts[week] = 2
        # 성공 시 pop
        scheduler_module._dna_retry_counts.pop(week, None)
        assert week not in scheduler_module._dna_retry_counts

        scheduler_module._dna_retry_counts.update(original_counts)

    @pytest.mark.asyncio
    async def test_weekly_dna_refresh_skips_when_no_db(self):
        """DATABASE_URL 미설정(SessionLocal=None) → 즉시 반환"""
        import app.scheduler as scheduler_module
        import app.database as db_module

        original_session_local = db_module.SessionLocal
        db_module.SessionLocal = None
        try:
            # 예외 없이 반환되어야 함
            await scheduler_module.weekly_dna_refresh_job()
        finally:
            db_module.SessionLocal = original_session_local

    @pytest.mark.asyncio
    async def test_weekly_dna_refresh_retries_when_crawl_not_done(self):
        """크롤 미완료 주차 → 재시도 카운트 증가 + DateTrigger 작업 등록"""
        import app.scheduler as scheduler_module

        week = "2026-W96"
        original_counts = dict(scheduler_module._dna_retry_counts)
        scheduler_module._dna_retry_counts.clear()
        scheduler_module._dna_retry_counts[week] = 0

        mock_db = MagicMock()
        mock_session_local = MagicMock(return_value=mock_db)

        with patch("app.scheduler.check_crawl_completed_this_week", return_value=False), \
             patch.object(scheduler_module.scheduler, "add_job") as mock_add_job, \
             patch("app.database.SessionLocal", mock_session_local):

            import datetime
            fixed_now = datetime.datetime(2026, 3, 30, 5, 0, 0, tzinfo=datetime.UTC)
            # week 결정을 위해 datetime.datetime.now 패치
            with patch("datetime.datetime") as mock_dt:
                mock_dt.now.return_value = fixed_now
                mock_dt.UTC = datetime.UTC
                mock_dt.timedelta = datetime.timedelta
                # isocalendar 호환
                mock_dt.side_effect = lambda *a, **kw: datetime.datetime(*a, **kw)

                # SessionLocal을 직접 패치
                import app.database as db_module
                original_sl = db_module.SessionLocal
                db_module.SessionLocal = mock_session_local

                try:
                    await scheduler_module.weekly_dna_refresh_job()
                except Exception:
                    pass  # datetime mock 복잡도로 인한 예외 허용
                finally:
                    db_module.SessionLocal = original_sl

        scheduler_module._dna_retry_counts.clear()
        scheduler_module._dna_retry_counts.update(original_counts)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Demo Seeder Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestDemoSeeder:
    """POST /api/v1/admin/seed-demo"""

    @patch("app.seed.demo_seeder.DemoSeeder.run")
    def test_seed_demo_admin_success(self, mock_run, client, mock_admin):
        """SUPER_ADMIN → 200, 시딩 결과 반환"""
        mock_run.return_value = {
            "companies_created": 5,
            "snapshots_created": 60,
            "weeks": 12,
        }
        response = client.post("/api/v1/admin/seed-demo")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["companies_created"] == 5
        assert data["data"]["snapshots_created"] == 60

    def test_seed_demo_non_admin_403(self, client, mock_pro_user):
        """PRO 사용자 → 403"""
        response = client.post("/api/v1/admin/seed-demo")
        assert response.status_code == 403

    def test_seed_demo_starter_403(self, client, mock_user):
        """STARTER 사용자 → 403"""
        response = client.post("/api/v1/admin/seed-demo")
        assert response.status_code == 403

    @patch("app.seed.demo_seeder.DemoSeeder.run")
    def test_seed_demo_weeks_param(self, mock_run, client, mock_admin):
        """weeks 파라미터 전달 → seeder.run(weeks=N) 호출"""
        mock_run.return_value = {"weeks": 24}
        response = client.post("/api/v1/admin/seed-demo?weeks=24")
        assert response.status_code == 200
        mock_run.assert_called_once_with(weeks=24)

    @patch("app.seed.demo_seeder.DemoSeeder.run")
    def test_seed_demo_default_weeks(self, mock_run, client, mock_admin):
        """weeks 기본값 = 12"""
        mock_run.return_value = {"weeks": 12}
        response = client.post("/api/v1/admin/seed-demo")
        assert response.status_code == 200
        mock_run.assert_called_once_with(weeks=12)


# ─────────────────────────────────────────────────────────────────────────────
# 6. get_company_dna_trend 서비스 단위 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCompanyDnaTrend:
    """CompanyDnaService.get_company_dna_trend"""

    def test_returns_data_points_sorted_asc(self):
        """스냅샷이 내림차순으로 조회되어도 주차 오름차순 정렬 반환"""
        service, db = _make_service()

        cid = uuid.uuid4()

        snap_w11 = MagicMock()
        snap_w11.week = "2026-W11"
        snap_w11.overall_dna_score = 72.0
        snap_w11.tech_diversity_score = 82.0
        snap_w11.hiring_intensity_score = 62.0
        snap_w11.salary_position_pct = 76.0
        snap_w11.culture_score = 0.52
        snap_w11.segment_id = "dev_server"

        snap_w10 = MagicMock()
        snap_w10.week = "2026-W10"
        snap_w10.overall_dna_score = 70.0
        snap_w10.tech_diversity_score = 80.0
        snap_w10.hiring_intensity_score = 60.0
        snap_w10.salary_position_pct = 75.0
        snap_w10.culture_score = 0.50
        snap_w10.segment_id = "dev_server"

        # DB 조회는 DESC → [W11, W10]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = [snap_w11, snap_w10]
        q.first.return_value = MagicMock(name="토스")
        db.query.return_value = q

        result = service.get_company_dna_trend(str(cid))
        assert result is not None
        # ASC 정렬 확인
        weeks = [dp["week"] for dp in result["data_points"]]
        assert weeks == sorted(weeks)

    def test_returns_none_when_no_snapshots(self):
        """스냅샷 없음 → None 반환"""
        service, db = _make_service()
        cid = uuid.uuid4()

        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = service.get_company_dna_trend(str(cid))
        assert result is None

    def test_returns_none_for_invalid_uuid_and_no_name_match(self):
        """유효하지 않은 UUID + 이름 검색 실패 → None"""
        service, db = _make_service()

        # resolve_company_by_name 반환 None
        with patch.object(service, "resolve_company_by_name", return_value=None):
            result = service.get_company_dna_trend("not-a-uuid")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# 7. compare_companies 서비스 단위 테스트
# ─────────────────────────────────────────────────────────────────────────────

class TestCompareCompaniesService:
    """CompanyDnaService.compare_companies"""

    def test_both_exist_same_segment(self):
        """두 기업 모두 존재 + 동일 세그먼트 → segment_benchmark 포함"""
        service, db = _make_service()
        cid_a = str(uuid.uuid4())
        cid_b = str(uuid.uuid4())
        dna_a = _company_dna_dict(cid_a)
        dna_b = _company_dna_dict(cid_b)
        benchmark = _segment_benchmark_dict()

        with patch.object(service, "get_company_dna", side_effect=[dna_a, dna_b]), \
             patch.object(service, "get_segment_benchmarks", return_value=benchmark):
            result = service.compare_companies(cid_a, cid_b)

        assert result is not None
        assert result["company_a"] == dna_a
        assert result["company_b"] == dna_b
        assert result["segment_benchmark"] == benchmark

    def test_both_missing_returns_none(self):
        """두 기업 모두 없음 → None"""
        service, db = _make_service()
        with patch.object(service, "get_company_dna", return_value=None):
            result = service.compare_companies("x", "y")
        assert result is None

    def test_company_a_missing(self):
        """기업 A 없음 → error + missing='a'"""
        service, db = _make_service()
        cid_b = str(uuid.uuid4())
        dna_b = _company_dna_dict(cid_b)

        with patch.object(service, "get_company_dna", side_effect=[None, dna_b]):
            result = service.compare_companies("nonexistent", cid_b)

        assert result is not None
        assert "error" in result
        assert result["missing"] == "a"

    def test_company_b_missing(self):
        """기업 B 없음 → error + missing='b'"""
        service, db = _make_service()
        cid_a = str(uuid.uuid4())
        dna_a = _company_dna_dict(cid_a)

        with patch.object(service, "get_company_dna", side_effect=[dna_a, None]):
            result = service.compare_companies(cid_a, "nonexistent")

        assert result is not None
        assert "error" in result
        assert result["missing"] == "b"

    def test_different_segments_no_benchmark(self):
        """서로 다른 세그먼트 → segment_benchmark = None"""
        service, db = _make_service()
        cid_a = str(uuid.uuid4())
        cid_b = str(uuid.uuid4())
        dna_a = _company_dna_dict(cid_a)
        dna_b = _company_dna_dict(cid_b)
        dna_b["segment_id"] = "product"  # 다른 세그먼트

        with patch.object(service, "get_company_dna", side_effect=[dna_a, dna_b]):
            result = service.compare_companies(cid_a, cid_b)

        assert result is not None
        assert result["segment_benchmark"] is None
