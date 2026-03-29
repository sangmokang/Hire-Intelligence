"""주간 크롤링 스케줄러 — APScheduler 3.x + FastAPI 연동"""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


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
        else:
            logger.warning(f"크롤 실패: status={crawl_run.status}")

    except Exception as e:
        logger.error(f"주간 크롤링 오류: {e}")
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
