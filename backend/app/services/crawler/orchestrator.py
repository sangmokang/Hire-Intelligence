"""크롤 오케스트레이터 — 크롤러 조율, 중복 제거, DB 저장"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.ops import Company, Position
from app.models.pulse import JdAnalysis, CrawlRun
from app.services.crawler.base import (
    normalize_company_name, is_duplicate_title, CrawlContext,
)
from app.services.crawler.wanted_crawler import WantedCrawler
from app.constants.segments import SEGMENTS

logger = logging.getLogger(__name__)


# CrawlOrchestrator 클래스 — 외부에서 인스턴스화 가능하도록 제공
class CrawlOrchestrator:
    """크롤 오케스트레이터 클래스 (편의 래퍼)"""

    async def run(
        self,
        db: Session,
        platform: str = "wanted",
        segment_id: str | None = None,
    ) -> CrawlRun:
        """run_crawl 위임"""
        return await run_crawl(db=db, platform=platform, segment_id=segment_id)


def get_current_week() -> str:
    """현재 ISO 주차 문자열 반환 (예: '2026-W13')"""
    now = datetime.now(timezone.utc)
    iso = now.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _resolve_or_create_company(db: Session, company_name: str) -> uuid.UUID:
    """회사명으로 기존 Company 조회 또는 신규 생성"""
    normalized = normalize_company_name(company_name)
    if not normalized:
        normalized = company_name.strip()

    # 정규화된 이름으로 검색
    company = db.execute(
        select(Company).where(Company.normalized_name == normalized)
    ).scalar_one_or_none()

    if company:
        return company.id

    # 신규 회사 생성
    new_company = Company(
        id=uuid.uuid4(),
        name=company_name.strip(),
        normalized_name=normalized,
        aliases=[],
    )
    db.add(new_company)
    db.flush()  # ID 확보
    logger.info(f"신규 회사 생성: {company_name} → {normalized}")
    return new_company.id


def check_crawl_running(db: Session) -> bool:
    """현재 실행 중인 크롤이 있는지 확인"""
    running = db.execute(
        select(CrawlRun).where(CrawlRun.status == "running")
    ).scalar_one_or_none()
    return running is not None


async def run_crawl(
    db: Session,
    platform: str = "wanted",
    segment_id: str | None = None,
    crawl_run: CrawlRun | None = None,
) -> CrawlRun:
    """크롤 실행 메인 함수

    Args:
        db: 데이터베이스 세션
        platform: 크롤링 대상 (wanted/saramin/all)
        segment_id: 특정 세그먼트만 (None = 전체)
        crawl_run: 사전 생성된 CrawlRun (None이면 새로 생성)
    """
    week = get_current_week()

    # 크롤 실행 기록 생성 또는 기존 레코드 사용
    if crawl_run is None:
        crawl_run = CrawlRun(
            id=uuid.uuid4(),
            started_at=datetime.now(timezone.utc),
            status="running",
            platform=platform,
            segment_id=segment_id,
            total_fetched=0,
            total_parsed=0,
            total_errors=0,
        )
        db.add(crawl_run)
    else:
        crawl_run.status = "running"
        crawl_run.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        # 대상 세그먼트 결정
        if segment_id:
            target_segments = [segment_id]
        else:
            target_segments = [s["id"] for s in SEGMENTS]

        # 기존 제목 목록 (중복 검사용)
        existing_titles_by_segment: dict[str, list[str]] = {}
        for seg in target_segments:
            titles = db.execute(
                select(Position.title).where(
                    Position.segment_id == seg,
                    Position.week == week,
                )
            ).scalars().all()
            existing_titles_by_segment[seg] = list(titles)

        total_context = CrawlContext()

        # 크롤러 실행
        crawlers: list = []
        if platform in ("wanted", "all"):
            crawlers.append(WantedCrawler())
        # Saramin은 stretch goal — 별도 import 시 추가
        if platform in ("saramin", "all"):
            try:
                from app.services.crawler.saramin_crawler import SaraminCrawler
                crawlers.append(SaraminCrawler())
            except ImportError:
                logger.warning("사람인 크롤러 미구현 — 건너뜀")

        for crawler in crawlers:
            for seg in target_segments:
                try:
                    # 1. 목록 수집
                    listings = await crawler.fetch_listings(seg)

                    for listing in listings:
                        title = listing.get("title", "")
                        company_name = listing.get("company_name", "")

                        if not title or not company_name:
                            continue

                        # 2. 중복 검사 (Jaccard >= 0.8)
                        existing = existing_titles_by_segment.get(seg, [])
                        if is_duplicate_title(title, existing):
                            total_context.total_skipped += 1
                            continue

                        # 3. 상세 페이지 수집
                        detail = await crawler.fetch_detail(listing)
                        if not detail:
                            continue

                        # 4. 회사 조회/생성
                        company_id = _resolve_or_create_company(db, company_name)

                        # 5. Position 저장
                        position = Position(
                            id=uuid.uuid4(),
                            company_id=company_id,
                            title=title,
                            segment_id=seg,
                            week=week,
                            platform=crawler.platform_name,
                            url=detail.get("url"),
                            salary_min=detail.get("salary_min"),
                            salary_max=detail.get("salary_max"),
                            raw_text=detail.get("raw_text", ""),
                        )
                        db.add(position)

                        # 6. JdAnalysis 레코드 생성 (파싱 대기)
                        jd_analysis = JdAnalysis(
                            id=uuid.uuid4(),
                            position_id=position.id,
                            company_id=company_id,
                            segment_id=seg,
                            platform=crawler.platform_name,
                            week=week,
                        )
                        db.add(jd_analysis)

                        # 기존 제목 목록에 추가 (후속 중복 검사용)
                        existing_titles_by_segment.setdefault(seg, []).append(title)
                        total_context.total_new += 1

                except Exception as e:
                    logger.error(f"세그먼트 크롤 실패 [{crawler.platform_name}/{seg}]: {e}")
                    total_context.total_errors += 1
                    total_context.errors.append({
                        "platform": crawler.platform_name,
                        "segment_id": seg,
                        "error": str(e),
                    })
                    # 세그먼트별 에러 격리 — 전체 크롤 중단하지 않음
                    continue

            total_context.total_fetched += crawler.context.total_fetched
            total_context.total_errors += crawler.context.total_errors

        # 크롤 완료 처리
        db.commit()
        crawl_run.status = "completed"
        crawl_run.finished_at = datetime.now(timezone.utc)
        crawl_run.total_fetched = total_context.total_fetched
        crawl_run.total_parsed = 0  # 파싱은 별도 단계
        crawl_run.total_errors = total_context.total_errors
        crawl_run.error_log = total_context.errors if total_context.errors else None
        db.commit()

        logger.info(
            f"크롤 완료: fetched={total_context.total_fetched}, "
            f"new={total_context.total_new}, "
            f"skipped={total_context.total_skipped}, "
            f"errors={total_context.total_errors}"
        )

    except Exception as e:
        logger.error(f"크롤 실행 치명적 오류: {e}")
        crawl_run.status = "failed"
        crawl_run.finished_at = datetime.now(timezone.utc)
        crawl_run.error_log = [{"error": str(e), "phase": "orchestrator"}]
        db.commit()

    return crawl_run
