"""크롤 트리거 및 상태 조회 라우터 (관리자 전용)"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from datetime import datetime, timezone

from app.database import get_db
from app.models.pulse import CrawlRun
from app.schemas.common import ApiResponse
from app.schemas.jd_analysis import CrawlTriggerRequest, CrawlTriggerResponse, CrawlStatusResponse
from app.services.crawler.orchestrator import run_crawl, check_crawl_running
from app.middleware.rbac import require_super_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["crawl"])


async def _background_crawl_and_parse(crawl_run_id: str, platform: str, segment_id: str | None):
    """백그라운드에서 크롤 + 파싱 실행 (사전 생성된 CrawlRun ID 사용)"""
    from app.database import SessionLocal
    if SessionLocal is None:
        logger.error("DATABASE_URL 미설정")
        return

    db = SessionLocal()
    try:
        # 사전 생성된 CrawlRun 레코드를 running으로 업데이트
        run_uuid = uuid.UUID(crawl_run_id)
        crawl_run = db.execute(
            select(CrawlRun).where(CrawlRun.id == run_uuid)
        ).scalar_one_or_none()

        if not crawl_run:
            logger.error(f"CrawlRun 미존재: {crawl_run_id}")
            return

        crawl_run.status = "running"
        db.commit()

        # 크롤 실행 (기존 crawl_run 전달)
        crawl_run = await run_crawl(db, platform=platform, segment_id=segment_id, crawl_run=crawl_run)

        # 파싱 실행
        if crawl_run.status == "completed":
            from app.services.jd_parser import JdParserService  # 런타임 임포트 (anthropic 의존성)
            parser = JdParserService()
            stats = parser.parse_batch(db, crawl_run_id=str(crawl_run.id))

            # 파싱 결과로 crawl_run 업데이트
            crawl_run.total_parsed = stats.get("success", 0)
            db.commit()
            logger.info(f"크롤+파싱 완료: crawl_run_id={crawl_run.id}")
    except Exception as e:
        logger.error(f"백그라운드 크롤+파싱 오류: {e}")
    finally:
        db.close()


@router.post(
    "/trigger",
    response_model=ApiResponse[CrawlTriggerResponse],
    dependencies=[Depends(require_super_admin)],
)
def trigger_crawl(
    request: CrawlTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """크롤 트리거 (관리자 전용) — 백그라운드에서 실행"""
    # 동시실행 가드
    if check_crawl_running(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 실행 중인 크롤이 있습니다. 완료 후 다시 시도하세요.",
        )

    # CrawlRun 레코드를 동기적으로 생성 (실제 ID 반환)
    crawl_run = CrawlRun(
        id=uuid.uuid4(),
        started_at=datetime.now(timezone.utc),
        status="pending",
        platform=request.platform,
        segment_id=request.segment_id,
        total_fetched=0,
        total_parsed=0,
        total_errors=0,
    )
    db.add(crawl_run)
    db.commit()

    # 백그라운드 태스크로 크롤+파싱 실행
    background_tasks.add_task(
        _background_crawl_and_parse,
        crawl_run_id=str(crawl_run.id),
        platform=request.platform,
        segment_id=request.segment_id,
    )

    return ApiResponse(
        data=CrawlTriggerResponse(
            crawl_run_id=str(crawl_run.id),
            status="pending",
            message=f"{request.platform} 크롤링이 시작되었습니다.",
        )
    )


@router.get(
    "/status/{crawl_run_id}",
    response_model=ApiResponse[CrawlStatusResponse],
    dependencies=[Depends(require_super_admin)],
)
def get_crawl_status(
    crawl_run_id: str,
    db: Session = Depends(get_db),
):
    """크롤 실행 상태 조회"""
    try:
        run_uuid = uuid.UUID(crawl_run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 crawl_run_id")

    crawl_run = db.execute(
        select(CrawlRun).where(CrawlRun.id == run_uuid)
    ).scalar_one_or_none()

    if not crawl_run:
        raise HTTPException(status_code=404, detail="크롤 실행 기록을 찾을 수 없습니다.")

    return ApiResponse(
        data=CrawlStatusResponse(
            crawl_run_id=str(crawl_run.id),
            status=crawl_run.status,
            platform=crawl_run.platform,
            segment_id=crawl_run.segment_id,
            total_fetched=crawl_run.total_fetched,
            total_parsed=crawl_run.total_parsed,
            total_errors=crawl_run.total_errors,
            started_at=crawl_run.started_at,
            finished_at=crawl_run.finished_at,
        )
    )
