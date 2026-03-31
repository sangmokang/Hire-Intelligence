"""주간 크롤링 스케줄러 — APScheduler 3.x + FastAPI 연동"""
import logging
from contextlib import asynccontextmanager

from app.services.notification import notifier

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# DNA refresh 재시도 관리
_dna_retry_counts: dict[str, int] = {}
DNA_REFRESH_MAX_RETRIES = 3


async def weekly_crawl_job():
    """주간 크롤링 작업 — 매주 월요일 03:00 KST 실행"""
    from app.database import SessionLocal
    from app.services.crawler.orchestrator import run_crawl, check_crawl_running
    from app.services.jd_parser import JdParserService

    if SessionLocal is None:
        logger.error("DATABASE_URL 미설정 — 스케줄 크롤 건너뜀")
        return

    db = SessionLocal()
    try:
        # 이미 실행 중인 크롤이 있으면 건너뜀
        if check_crawl_running(db):
            logger.warning("이미 실행 중인 크롤이 있어 스케줄 크롤 건너뜀")
            return

        logger.info("주간 크롤링 시작")
        crawl_run = await run_crawl(db, platform="wanted")

        # 파싱 실행
        if crawl_run.status == "completed":
            parser = JdParserService()
            stats = parser.parse_batch(db)
            crawl_run.total_parsed = stats.get("success", 0)
            db.commit()
            logger.info(f"주간 크롤+파싱 완료: {stats}")
            # 크롤 성공 알림 전송
            import datetime as _dt
            _now = _dt.datetime.now(_dt.UTC)
            _week = f"{_now.isocalendar()[0]}-W{_now.isocalendar()[1]:02d}"
            await notifier.send_crawl_success(
                platform="wanted",
                count=crawl_run.total_fetched,
                week=_week,
            )
        else:
            logger.warning(f"크롤 실패: status={crawl_run.status}")
            # 크롤 상태 실패 알림 전송
            await notifier.send_crawl_failure(
                platform="wanted",
                error=f"status={crawl_run.status}",
            )

    except Exception as e:
        logger.error(f"주간 크롤링 오류: {e}")
        # 예외 발생 시 크롤 실패 알림 전송
        await notifier.send_crawl_failure(platform="wanted", error=str(e))
    finally:
        db.close()


def check_crawl_completed_this_week(db: Session, week: str) -> bool:
    """해당 주차의 크롤링+파싱이 완료되었는지 확인"""
    from app.models.pulse import JdAnalysis
    count = db.query(func.count(JdAnalysis.id)).filter(
        JdAnalysis.week == week,
        JdAnalysis.parsed_at.isnot(None)
    ).scalar()
    return count is not None and count > 0


async def weekly_dna_refresh_job():
    """주간 DNA 스냅샷 갱신 — 크롤 미완료 시 최대 3회 재시도 (1시간 간격)"""
    from app.database import SessionLocal
    from app.services.company_dna_service import CompanyDnaService
    import datetime

    if SessionLocal is None:
        logger.error("DATABASE_URL 미설정 — DNA 갱신 건너뜀")
        return

    # week를 try 외부에서 초기화 — except 블록에서 안전하게 참조 가능
    now = datetime.datetime.now(datetime.UTC)
    week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"

    db = SessionLocal()
    try:
        if not check_crawl_completed_this_week(db, week):
            retry_count = _dna_retry_counts.get(week, 0)
            if retry_count < DNA_REFRESH_MAX_RETRIES:
                _dna_retry_counts[week] = retry_count + 1
                # 1시간 후 재시도 스케줄
                from apscheduler.triggers.date import DateTrigger
                next_run = now + datetime.timedelta(hours=1)
                scheduler.add_job(
                    weekly_dna_refresh_job,
                    trigger=DateTrigger(run_date=next_run),
                    id=f'dna_refresh_retry_{week}_{retry_count + 1}',
                    replace_existing=True,
                )
                logger.warning(f"Week {week} crawl not ready, retry {retry_count + 1}/{DNA_REFRESH_MAX_RETRIES} scheduled")
            else:
                logger.error(f"Week {week} DNA refresh: {DNA_REFRESH_MAX_RETRIES}회 재시도 소진")
                # 재시도 횟수 소진 시 실패 알림 전송
                await notifier.send_dna_refresh_result(
                    week=week,
                    success=False,
                    detail=f"{DNA_REFRESH_MAX_RETRIES}회 재시도 소진",
                )
            return

        # 크롤 완료 — DNA 갱신 실행
        service = CompanyDnaService(db)
        result = service.refresh_all(week)
        logger.info(f"DNA refresh completed for {week}: {result}")
        # 성공 시 재시도 카운트 초기화
        _dna_retry_counts.pop(week, None)
        # DNA 갱신 성공 알림 전송
        await notifier.send_dna_refresh_result(week=week, success=True, detail=str(result))
    except Exception as e:
        logger.error(f"DNA refresh failed: {e}")
        # 예외 발생 시 DNA 갱신 실패 알림 전송
        await notifier.send_dna_refresh_result(week=week, success=False, detail=str(e))
    finally:
        db.close()


def init_scheduler():
    """스케줄러 초기화 — 주간 크롤 작업 등록"""
    # 매주 월요일 03:00 KST (= 일요일 18:00 UTC)
    scheduler.add_job(
        weekly_crawl_job,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=0, timezone="Asia/Seoul"),
        id="weekly_crawl",
        name="주간 JD 크롤링",
        replace_existing=True,
    )
    logger.info("주간 크롤링 스케줄 등록: 매주 월요일 03:00 KST")

    # 매주 월요일 05:00 KST — DNA 갱신 (크롤+파싱 완료 후 2시간 버퍼)
    scheduler.add_job(
        weekly_dna_refresh_job,
        CronTrigger(day_of_week='mon', hour=5, minute=0, timezone='Asia/Seoul'),
        id='company_dna_refresh',
        replace_existing=True,
    )
    logger.info("DNA 갱신 스케줄 등록: 매주 월요일 05:00 KST")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 라이프사이클 — 스케줄러 시작/종료"""
    # 프로덕션에서만 스케줄러 실행
    if settings.APP_ENV != "test":
        init_scheduler()
        scheduler.start()
        logger.info("스케줄러 시작됨")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("스케줄러 종료됨")
