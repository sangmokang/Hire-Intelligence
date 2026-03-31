from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.middleware.rbac import require_super_admin
from app.schemas.common import ApiResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=ApiResponse[list])
async def list_users(current_user: dict = Depends(require_super_admin)):
    """전체 사용자 목록 (관리자 전용)"""
    # TODO: DB 연동 후 실제 구현
    return ApiResponse(data=[], message="사용자 목록")


@router.get("/stats", response_model=ApiResponse[dict])
async def get_stats(current_user: dict = Depends(require_super_admin)):
    """플랫폼 통계 (관리자 전용)"""
    return ApiResponse(
        data={
            "total_users": 0,
            "active_users": 0,
            "total_organizations": 0,
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
