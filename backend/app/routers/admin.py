from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from supabase import Client

from app.database import get_db
from app.dependencies import get_supabase_client
from app.middleware.rbac import require_super_admin
from app.schemas.admin import AnomalyItem, CrawlStatusResponse, DataQualityResponse, WeeklyCollectionStats
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=ApiResponse[list])
async def list_users(
    current_user: dict = Depends(require_super_admin),
    supabase: Client = Depends(get_supabase_client),
):
    """전체 사용자 목록 (관리자 전용)"""
    result = (
        supabase.table("user_profiles")
        .select(
            "id, email, name, phone, company, job_title, profile_image_url, "
            "role, category, status, plan, organization_id, last_login_at, login_count, created_at"
        )
        .limit(100)
        .order("created_at", desc=True)
        .execute()
    )
    return ApiResponse(data=result.data or [], message="사용자 목록")


@router.get("/stats", response_model=ApiResponse[dict])
async def get_stats(
    current_user: dict = Depends(require_super_admin),
    supabase: Client = Depends(get_supabase_client),
):
    """플랫폼 통계 (관리자 전용)"""
    all_users = supabase.table("user_profiles").select("status, organization_id").execute()
    rows = all_users.data or []
    total_users = len(rows)
    active_users = sum(1 for r in rows if r.get("status") == "ACTIVE")
    org_ids = {r.get("organization_id") for r in rows if r.get("organization_id")}
    return ApiResponse(
        data={
            "totalUsers": total_users,
            "activeUsers": active_users,
            "totalOrganizations": len(org_ids),
        }
    )


@router.post("/seed-demo", response_model=ApiResponse[dict])
def seed_demo_data(
    weeks: int = Query(12, ge=4, le=52),
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """데모 데이터 시딩 (SUPER_ADMIN 전용) — B2B 프레젠테이션용"""
    from app.seed.demo_seeder import DemoSeeder
    seeder = DemoSeeder(db)
    result = seeder.run(weeks=weeks)
    return ApiResponse(data=result)


@router.post("/backfill-dna", response_model=ApiResponse[dict])
def backfill_dna(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """DNA 스냅샷 전체 백필 (SUPER_ADMIN 전용) — cold start 대응"""
    from app.services.company_dna_service import CompanyDnaService
    service = CompanyDnaService(db)
    result = service.backfill_all_weeks()
    return ApiResponse(data=result)


# 14개 직군 목록 — 전체 세그먼트 기준
_ALL_SEGMENTS: list[str] = [
    "software_engineer",
    "frontend_engineer",
    "backend_engineer",
    "data_engineer",
    "data_scientist",
    "ml_engineer",
    "devops_engineer",
    "product_manager",
    "designer",
    "marketing",
    "sales",
    "finance",
    "hr",
    "operations",
]


@router.get("/data-quality", response_model=ApiResponse[DataQualityResponse])
def get_data_quality(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """데이터 품질 모니터링 — 최근 4주 수집 현황 및 이상치 탐지 (SUPER_ADMIN 전용)"""
    from app.models.pulse import JobPosting, SegmentSnapshot

    # 현재 주 계산 (ISO 8601 형식: YYYY-Www)
    now = datetime.now(timezone.utc)
    current_week = now.strftime("%G-W%V")

    # 최근 4주 목록 생성 — DB에서 실제 존재하는 주차를 내림차순으로 최대 4개 조회
    week_rows = (
        db.query(JobPosting.week)
        .distinct()
        .order_by(JobPosting.week.desc())
        .limit(4)
        .all()
    )
    recent_weeks: list[str] = [r.week for r in week_rows]

    # 주차별 통계 집계
    weekly_stats: list[WeeklyCollectionStats] = []
    for week in sorted(recent_weeks):  # 오름차순 정렬하여 anomaly 비교를 순서대로 처리
        # 총 채용 공고 수 (count 컬럼 합산)
        total_postings: int = db.query(func.coalesce(func.sum(JobPosting.count), 0)).filter(
            JobPosting.week == week
        ).scalar() or 0

        # 채용한 기업 수 (distinct company_id)
        total_companies: int = db.query(func.count(distinct(JobPosting.company_id))).filter(
            JobPosting.week == week
        ).scalar() or 0

        # 해당 주에 데이터 있는 직군 수 (SegmentSnapshot 기준)
        segments_covered: int = db.query(func.count(distinct(SegmentSnapshot.segment_id))).filter(
            SegmentSnapshot.week == week
        ).scalar() or 0

        weekly_stats.append(
            WeeklyCollectionStats(
                week=week,
                total_postings=total_postings,
                total_companies=total_companies,
                segments_covered=segments_covered,
                segments_total=len(_ALL_SEGMENTS),
            )
        )

    # 이번 주 데이터 없는 직군명 계산
    current_week_segment_rows = (
        db.query(SegmentSnapshot.segment_id)
        .filter(SegmentSnapshot.week == current_week)
        .distinct()
        .all()
    )
    covered_this_week = {r.segment_id for r in current_week_segment_rows}
    missing_segments: list[str] = [s for s in _ALL_SEGMENTS if s not in covered_this_week]

    # 이상치 탐지 — 전주 대비 total_postings ±50% 변동
    anomalies: list[AnomalyItem] = []
    for i in range(1, len(weekly_stats)):
        prev = weekly_stats[i - 1]
        curr = weekly_stats[i]
        if prev.total_postings > 0:
            change_ratio = (curr.total_postings - prev.total_postings) / prev.total_postings
            if abs(change_ratio) >= 0.5:
                anomalies.append(AnomalyItem(
                    week=curr.week,
                    prev_week=prev.week,
                    prev_total_postings=prev.total_postings,
                    curr_total_postings=curr.total_postings,
                    change_pct=round(change_ratio * 100, 1),
                ))

    return ApiResponse(
        data=DataQualityResponse(
            current_week=current_week,
            weekly_stats=weekly_stats,
            missing_segments=missing_segments,
            anomalies=anomalies,
        )
    )


@router.get("/crawl-status", response_model=ApiResponse[CrawlStatusResponse])
def get_crawl_status(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """최근 크롤 실행 상태 조회 (SUPER_ADMIN 전용)"""
    from app.models.pulse import CrawlRun

    # 가장 최근 크롤 실행 기록 조회
    last_run: CrawlRun | None = (
        db.query(CrawlRun)
        .order_by(CrawlRun.started_at.desc())
        .first()
    )

    if last_run is None:
        return ApiResponse(
            data=CrawlStatusResponse(
                last_crawl_at=None,
                last_crawl_status=None,
                total_crawled=0,
                total_parsed=0,
                next_scheduled="매주 월요일 03:00 KST",
            )
        )

    return ApiResponse(
        data=CrawlStatusResponse(
            last_crawl_at=last_run.started_at,
            last_crawl_status=last_run.status,
            total_crawled=last_run.total_fetched,
            total_parsed=last_run.total_parsed,
            next_scheduled="매주 월요일 03:00 KST",
        )
    )
