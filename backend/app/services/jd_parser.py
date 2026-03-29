"""JD 텍스트 LLM 파서 — Claude Haiku로 6개 카테고리 구조화 추출"""
import json
import logging
from datetime import datetime, timezone

import anthropic
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.models.pulse import JdAnalysis, CrawlRun
from app.models.ops import Position

logger = logging.getLogger(__name__)

# JD 파싱 시스템 프롬프트
SYSTEM_PROMPT = """당신은 채용공고(JD) 텍스트에서 구조화된 정보를 추출하는 전문 파서입니다.
주어진 JD 텍스트를 분석하여 아래 6개 카테고리로 정확히 추출하세요.
반드시 JSON 형식으로만 응답하세요. 정보가 없는 필드는 null로 표시하세요.

출력 JSON 스키마:
{
  "tech_stack": ["Python", "FastAPI", ...],
  "experience": {
    "min_years": 3,
    "max_years": 7,
    "level": "senior"
  },
  "compensation": {
    "salary_min": 5000,
    "salary_max": 8000,
    "has_equity": false,
    "benefits": ["유연근무", "점심제공"]
  },
  "role_keywords": ["설계", "코드리뷰", "멘토링"],
  "domain_knowledge": ["핀테크", "결제"],
  "org_signals": {
    "team_size": "10-15명",
    "is_new_position": true,
    "growth_stage": "scale-up"
  }
}

규칙:
- tech_stack: 언급된 기술/도구/프레임워크 목록 (중복 제거)
- experience.level: junior/mid/senior/lead/exec 중 하나
- compensation.salary_min/max: 만원 단위 (예: 5000 = 5000만원)
- role_keywords: 핵심 역할/책임 키워드 (최대 10개)
- domain_knowledge: 필요한 도메인/산업 지식 (최대 5개)
- org_signals.growth_stage: startup/scale-up/enterprise 중 하나
- 정보가 없으면 해당 필드를 null로 설정"""

USER_PROMPT_TEMPLATE = """아래 채용공고 텍스트를 분석하세요:

---
{jd_text}
---

위 JD에서 6개 카테고리 정보를 추출하여 JSON으로 응답하세요."""


class JdParserService:
    """JD 텍스트 → 구조화 데이터 파서"""

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY 미설정 — JD 파싱 비활성화")
            self._client = None
        else:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def parse_jd(self, jd_text: str) -> dict | None:
        """단일 JD 텍스트 파싱

        Returns:
            파싱된 6개 카테고리 딕셔너리 또는 None (실패 시)
        """
        if not self._client:
            logger.error("Anthropic 클라이언트 미초기화")
            return None

        if not jd_text or not jd_text.strip():
            return None

        # 입력 텍스트 절삭 (최대 4000자 — Haiku 컨텍스트 여유 확보)
        truncated = jd_text[:4000]

        try:
            response = self._client.messages.create(
                model=settings.JD_PARSER_MODEL,
                max_tokens=1024,
                temperature=0.0,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(jd_text=truncated),
                }],
            )

            # 응답에서 JSON 추출
            raw_content = response.content[0].text.strip()

            # JSON 블록 마커 제거
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                # ``` 또는 ```json 첫 줄 제거
                lines = lines[1:]
                # 마지막 ``` 제거
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw_content = "\n".join(lines)

            parsed = json.loads(raw_content)

            # 토큰 사용량 로깅 (비용 모니터링용)
            usage = response.usage
            logger.info(
                f"JD 파싱 완료 — input_tokens={usage.input_tokens}, "
                f"output_tokens={usage.output_tokens}"
            )

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"JD 파싱 JSON 디코드 실패: {e}")
            return None
        except anthropic.APIError as e:
            logger.error(f"Anthropic API 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"JD 파싱 예상치 못한 오류: {e}")
            return None

    def _apply_parsed_data(self, analysis: JdAnalysis, parsed: dict) -> None:
        """파싱 결과를 JdAnalysis 레코드에 적용"""
        analysis.parsed_data = parsed
        analysis.model_used = settings.JD_PARSER_MODEL
        analysis.parsed_at = datetime.now(timezone.utc)

        # tech_stacks 추출
        analysis.tech_stacks = parsed.get("tech_stack", [])

        # experience 추출
        exp = parsed.get("experience") or {}
        analysis.experience_min = exp.get("min_years")
        analysis.experience_max = exp.get("max_years")
        analysis.role_level = exp.get("level")

        # compensation 추출
        comp = parsed.get("compensation") or {}
        if comp.get("salary_min") is not None:
            analysis.salary_min = comp["salary_min"]
        if comp.get("salary_max") is not None:
            analysis.salary_max = comp["salary_max"]

        # domain_knowledge 추출
        analysis.domain_tags = parsed.get("domain_knowledge", [])

    def parse_batch(self, db: Session, crawl_run_id: str | None = None) -> dict:
        """미파싱 JdAnalysis 레코드 배치 파싱

        Args:
            db: 데이터베이스 세션
            crawl_run_id: 특정 크롤 실행에 연결된 분석만 (None = 전부)

        Returns:
            {"total": N, "success": N, "failed": N}
        """
        batch_size = settings.JD_PARSER_BATCH_SIZE

        # 미파싱 레코드 조회
        query = select(JdAnalysis).where(JdAnalysis.parsed_at.is_(None))

        # crawl_run_id가 주어지면 해당 크롤 실행 이후 생성된 레코드만 처리
        if crawl_run_id is not None:
            crawl_run = db.execute(
                select(CrawlRun).where(CrawlRun.id == crawl_run_id)
            ).scalar_one_or_none()
            if crawl_run:
                query = query.where(JdAnalysis.created_at >= crawl_run.started_at)

        unparsed = db.execute(query).scalars().all()

        stats = {"total": len(unparsed), "success": 0, "failed": 0}
        logger.info(f"배치 파싱 시작: {stats['total']}건")

        for analysis in unparsed:
            # JD 텍스트 조회: position_id가 있으면 Position.raw_text, 없으면 자체 raw_text
            jd_text = None
            if analysis.position_id:
                position = db.execute(
                    select(Position).where(Position.id == analysis.position_id)
                ).scalar_one_or_none()
                if position:
                    jd_text = position.raw_text

            if not jd_text:
                jd_text = analysis.raw_text

            if not jd_text:
                logger.warning(f"JD 텍스트 없음 — analysis_id={analysis.id}")
                stats["failed"] += 1
                continue

            # 파싱 실행 (개별 실패가 배치 전체를 중단시키지 않도록 처리)
            parsed = self.parse_jd(jd_text)
            if parsed:
                self._apply_parsed_data(analysis, parsed)
                stats["success"] += 1
            else:
                stats["failed"] += 1

            # 배치 단위 커밋
            if (stats["success"] + stats["failed"]) % batch_size == 0:
                db.commit()
                logger.info(f"배치 커밋: {stats['success']}/{stats['total']}")

        # 최종 커밋
        db.commit()
        logger.info(f"배치 파싱 완료: {stats}")
        return stats
