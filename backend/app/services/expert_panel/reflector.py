"""RLVR Skill Reflector — 피드백 기반 전문가 프롬프트 자동 개선 배치"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models.expert_knowledge import ExpertFeedback, ExpertKnowledge, ExpertSession
from app.services.expert_panel.registry import ExpertType, EXPERT_PERSONAS, get_expert

logger = logging.getLogger(__name__)

# EMA 가중치 — 최근 피드백에 30% 가중치 적용
EMA_ALPHA = 0.3


def update_confidence(current_confidence: float, new_rating: int) -> float:
    """EMA 기반 confidence 업데이트.

    new_rating: 1~5 (사용자 평가)
    반환: 업데이트된 confidence 값 (0.0~1.0)

    예시: 초기 0.5에서 rating=5 → 0.3*1.0 + 0.7*0.5 = 0.65
    """
    score_new = (new_rating - 1) / 4.0  # 1→0.0, 2→0.25, 3→0.5, 4→0.75, 5→1.0
    new_conf = EMA_ALPHA * score_new + (1 - EMA_ALPHA) * current_confidence
    return round(new_conf, 3)


def build_expert_prompt(expert_type: ExpertType, learned_section: str | None = None) -> str:
    """정적 persona + 동적 학습 컨텍스트를 결합하여 최종 system prompt 생성.

    learned_section은 ExpertReflector가 사전에 DB에서 조회하여 생성한 문자열.
    프롬프트 구성 함수는 DB 핸들 불필요.
    """
    persona = get_expert(expert_type)
    base_prompt = persona.system_prompt

    if not learned_section:
        return base_prompt

    return base_prompt + learned_section


class ExpertReflector:
    """RLVR 반영기 — 피드백 집계 → 패턴 추출 → knowledge 업데이트"""

    def __init__(self, db: Session):
        self.db = db

    def run(self) -> dict:
        """전체 전문가에 대해 RLVR 반영 실행. 반환: {"processed": N, "skipped": M}"""
        processed = 0
        skipped = 0

        for expert_type in ExpertType:
            feedbacks = self._get_recent_feedbacks(expert_type, days=30)

            # 전문가별 최소 피드백 threshold
            if len(feedbacks) < settings.EXPERT_REFLECTOR_MIN_FEEDBACKS:
                skipped += 1
                continue

            self._analyze_and_update(expert_type, feedbacks)
            processed += 1

        self.db.commit()
        result = {"processed": processed, "skipped": skipped}
        logger.info(f"RLVR Reflector 완료: {result}")
        return result

    def _get_recent_feedbacks(self, expert_type: ExpertType, days: int = 30) -> list[ExpertFeedback]:
        """최근 N일간 특정 전문가의 피드백 조회"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return self.db.query(ExpertFeedback).filter(
            ExpertFeedback.expert_type == expert_type.value,
            ExpertFeedback.created_at >= cutoff,
            ExpertFeedback.rating.isnot(None),  # 명시적 rating이 있는 것만
        ).all()

    def _analyze_and_update(self, expert_type: ExpertType, feedbacks: list[ExpertFeedback]) -> None:
        """피드백 분석 → knowledge 테이블 업데이트"""
        # 성공 패턴 (rating >= 4) / 실패 패턴 (rating <= 2) 분리
        successes = [f for f in feedbacks if f.rating and f.rating >= 4]
        corrections = [f for f in feedbacks if f.rating and f.rating <= 2]

        # 성공 패턴 저장/업데이트
        if successes:
            self._upsert_pattern(
                expert_type=expert_type,
                pattern_type="SUCCESS",
                feedbacks=successes,
            )

        # 실패 패턴 저장/업데이트
        if corrections:
            self._upsert_pattern(
                expert_type=expert_type,
                pattern_type="CORRECTION",
                feedbacks=corrections,
            )

    def _upsert_pattern(
        self,
        expert_type: ExpertType,
        pattern_type: str,
        feedbacks: list[ExpertFeedback],
    ) -> None:
        """패턴을 expert_knowledge 테이블에 upsert"""
        # 피드백에서 관련 세션의 질문 패턴 추출
        session_ids = {f.session_id for f in feedbacks}
        sessions = self.db.query(ExpertSession).filter(
            ExpertSession.id.in_(session_ids)
        ).all()

        if not sessions:
            return

        # 질문 패턴 요약 (세션들의 질문을 결합)
        queries = [s.query[:100] for s in sessions[:5]]  # 최근 5개 세션의 질문
        query_pattern = " | ".join(queries)
        query_hash = hashlib.sha256(
            f"{expert_type.value}:{pattern_type}:{query_pattern}".encode()
        ).hexdigest()

        # 학습된 응답 패턴 생성
        if pattern_type == "SUCCESS":
            learned = f"이 전문가는 다음 유형의 질문에서 높은 평가를 받았습니다: {query_pattern}"
        else:
            feedback_texts = [f.feedback_text for f in feedbacks if f.feedback_text]
            if feedback_texts:
                learned = f"개선 필요 피드백: {'; '.join(feedback_texts[:3])}"
            else:
                learned = f"다음 유형의 질문에서 낮은 평가를 받았습니다: {query_pattern}"

        # 평균 rating으로 confidence 계산
        avg_rating = sum(f.rating for f in feedbacks if f.rating) / len(feedbacks)

        # 기존 knowledge 조회 (upsert)
        existing = self.db.query(ExpertKnowledge).filter(
            ExpertKnowledge.expert_type == expert_type.value,
            ExpertKnowledge.pattern_type == pattern_type,
            ExpertKnowledge.query_pattern_hash == query_hash,
        ).first()

        if existing:
            # EMA 업데이트
            existing.confidence_score = update_confidence(
                float(existing.confidence_score), int(avg_rating)
            )
            existing.usage_count += len(feedbacks)
            if pattern_type == "SUCCESS":
                existing.positive_count += len(feedbacks)
            else:
                existing.negative_count += len(feedbacks)
            existing.learned_response = learned
            existing.last_used_at = datetime.now(timezone.utc)
        else:
            # 새 knowledge 생성
            initial_confidence = (avg_rating - 1) / 4.0  # 1~5 → 0.0~1.0
            knowledge = ExpertKnowledge(
                expert_type=expert_type.value,
                pattern_type=pattern_type,
                query_pattern=query_pattern,
                query_pattern_hash=query_hash,
                learned_response=learned,
                confidence_score=round(initial_confidence, 3),
                usage_count=len(feedbacks),
                positive_count=len(feedbacks) if pattern_type == "SUCCESS" else 0,
                negative_count=len(feedbacks) if pattern_type == "CORRECTION" else 0,
            )
            self.db.add(knowledge)

    def get_learned_section(self, expert_type: ExpertType) -> str | None:
        """특정 전문가의 학습된 지침 섹션 생성 — confidence >= 0.7인 것만, 최대 5건"""
        knowledge_items = self.db.query(ExpertKnowledge).filter(
            ExpertKnowledge.expert_type == expert_type.value,
            ExpertKnowledge.confidence_score >= 0.7,
        ).order_by(ExpertKnowledge.confidence_score.desc()).limit(5).all()

        if not knowledge_items:
            return None

        learned_section = "\n\n---\n[학습된 지침 — 과거 사용자 피드백 기반]\n"
        for k in knowledge_items:
            prefix = "✓ 성공 패턴" if k.pattern_type == "SUCCESS" else "⚠ 개선 필요"
            learned_section += f"- [{prefix}] {k.learned_response}\n"

        return learned_section
