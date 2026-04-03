"""Expert Panel 서비스 — 분류 → 라우팅 → 병렬 Claude 호출 → 응답 조합"""
import asyncio
import hashlib
import json
import logging
import time
import uuid

import anthropic

from app.config import settings
from app.schemas.expert_panel import QueryClassification
from app.services.expert_panel.classifier import QueryClassifier
from app.services.expert_panel.registry import ExpertType, get_expert, EXPERT_PERSONAS
from app.services.expert_panel.router import ExpertRouter, RoutingStrategy

logger = logging.getLogger(__name__)


class ExpertPanelService:
    """Expert Panel 메인 오케스트레이터 — async"""

    def __init__(self) -> None:
        self.classifier = QueryClassifier()
        self.router = ExpertRouter()
        # AsyncAnthropic 사용 — asyncio 이벤트 루프 차단 방지
        self._client: anthropic.AsyncAnthropic | None = None
        if settings.ANTHROPIC_API_KEY:
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def ask(self, query: str, view: str | None, expert_hint: ExpertType | None,
                  context_data: dict | None, user: dict) -> dict:
        """메인 /ask 파이프라인 — 분류 → 라우팅 → 병렬 호출 → 응답"""
        start_time = time.time()

        # 0. 캐시 체크 — 캐시 히트 시 한도 소비 없이 즉시 반환
        cache_key = self._build_cache_key(query, view, user.get("category"), expert_hint)
        cached = await self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 1. 플랜별 일일 사용량 체크 (캐시 미스 시에만 소비)
        self._check_daily_limit(user)

        # 2. 분류 (Haiku) — expert_hint가 있으면 건너뛰기
        if expert_hint:
            from app.schemas.expert_panel import QueryAxis, QuerySpecificity
            classification = QueryClassification(
                axis=QueryAxis.TASK,
                specificity=QuerySpecificity.CONCRETE,
                confidence=1.0,
                selected_experts=[expert_hint],
                reasoning=f"USER_SPECIFIED: {expert_hint.value}",
            )
            experts = [expert_hint]
            strategy_name = "SINGLE_EXPERT_EXECUTION"
        else:
            classification = await self.classifier.classify(
                query=query,
                view=view,
                user_category=user.get("category"),
            )
            experts, strategy = self.router.route(classification, query)
            strategy_name = strategy.name

        # 3. 병렬 Claude 호출
        responses = await self._call_experts_parallel(experts, query, view, context_data, strategy_name)

        # 4. 폴백: 모든 전문가 실패 시 rule-based
        if not responses:
            responses = [self._rule_based_response(experts[0] if experts else ExpertType.CPO, query)]

        # 5. 세션 저장 및 ID 발급
        session_id = self._save_session(
            query=query,
            view=view,
            user=user,
            classification={
                "axis": classification.axis.value,
                "specificity": classification.specificity.value,
                "confidence": classification.confidence,
            },
            experts=experts,
            strategy_name=strategy_name,
            response_time_ms=int((time.time() - start_time) * 1000),
            is_cache_hit=False,
            is_fallback=not any(r.get("is_ai", True) for r in responses),
        )

        # 6. 사용량 기록
        self._record_usage(user)

        elapsed_ms = int((time.time() - start_time) * 1000)

        result = {
            "classification": {
                "axis": classification.axis.value,
                "specificity": classification.specificity.value,
                "confidence": classification.confidence,
                "routing_strategy": strategy_name,
            },
            "responses": responses,
            "session_id": session_id,
            "is_ai_generated": any(r.get("is_ai", True) for r in responses),
            "response_time_ms": elapsed_ms,
            "is_cache_hit": False,
            "is_fallback": not any(r.get("is_ai", True) for r in responses),
        }

        # 캐시 저장
        await self._save_to_cache(cache_key, result)

        return result

    async def _call_experts_parallel(
        self, experts: list[ExpertType], query: str, view: str | None,
        context_data: dict | None, strategy_name: str,
    ) -> list[dict]:
        """asyncio.gather로 전문가 병렬 호출 — 개별 실패 시 나머지 유지"""
        if not self._client:
            return []

        # 전략별 응답 모드 설정
        response_instruction = {
            "MULTI_EXPERT_BRAINSTORM": "다양한 관점에서 종합적으로 분석하고, 당신의 전문 분야 시각에서 핵심 의견과 실행 가능한 제안을 제시하세요.",
            "SINGLE_EXPERT_EXECUTION": "상세한 실행 계획과 단계별 가이드를 제공하세요.",
            "ANALYST_RESEARCH": "데이터 기반으로 분석하고, 수치와 트렌드를 중심으로 인사이트를 제공하세요.",
            "EXPERT_LOOKUP": "핵심만 간결하게 답변하세요. 3~5문장 이내.",
        }.get(strategy_name, "전문적인 분석과 실행 가능한 제안을 제공하세요.")

        async def _call_one(expert_type: ExpertType) -> dict | None:
            try:
                persona = get_expert(expert_type)
                system_prompt = persona.system_prompt + f"\n\n[응답 지침] {response_instruction}"

                user_msg = f"질문: {query}"
                if view:
                    user_msg += f"\n현재 뷰: {view}"
                if context_data:
                    user_msg += f"\n현재 데이터: {json.dumps(context_data, ensure_ascii=False)[:2000]}"

                # await로 비동기 호출 — 이벤트 루프 차단 방지
                response = await self._client.messages.create(
                    model=settings.EXPERT_PANEL_RESPONSE_MODEL,
                    max_tokens=1500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_msg}],
                    timeout=float(settings.EXPERT_PANEL_TIMEOUT),
                )
                answer = response.content[0].text
                return {
                    "expert": expert_type.value,
                    "expert_name": persona.name,
                    "answer": answer,
                    "confidence": 0.8,
                    "suggested_actions": None,
                    "related_views": persona.related_views,
                    "is_ai": True,
                }
            except Exception as e:
                logger.warning(f"전문가 {expert_type.value} 호출 실패: {e}")
                return None

        results = await asyncio.gather(
            *[_call_one(e) for e in experts],
            return_exceptions=True,
        )

        # 성공한 응답만 필터
        return [r for r in results if isinstance(r, dict) and r is not None]

    def _rule_based_response(self, expert_type: ExpertType, query: str) -> dict:
        """Claude API 실패 시 rule-based 폴백 응답"""
        persona = get_expert(expert_type)
        return {
            "expert": expert_type.value,
            "expert_name": persona.name,
            "answer": f"[{persona.name}] 현재 AI 분석이 일시적으로 불가합니다. "
                      f"{persona.domain} 관점에서 '{query[:50]}...'에 대해 "
                      f"관련 대시보드 뷰({', '.join(persona.related_views[:3])})를 확인해보시기 바랍니다.",
            "confidence": 0.3,
            "suggested_actions": None,
            "related_views": persona.related_views,
            "is_ai": False,
        }

    def _save_session(self, query: str, view: str | None, user: dict,
                      classification: dict, experts: list, strategy_name: str,
                      response_time_ms: int, is_cache_hit: bool, is_fallback: bool) -> str:
        """세션을 DB에 저장하고 session_id 반환"""
        from app.database import SessionLocal
        from app.models.expert_knowledge import ExpertSession

        db = SessionLocal()
        try:
            session = ExpertSession(
                user_id=user["id"],
                query=query,
                view=view,
                user_category=user.get("category"),
                classification_axis=classification["axis"],
                classification_specificity=classification["specificity"],
                classification_confidence=classification["confidence"],
                selected_experts=[e.value if hasattr(e, 'value') else e for e in experts],
                routing_strategy=strategy_name,
                response_time_ms=response_time_ms,
                is_cache_hit=is_cache_hit,
                is_fallback=is_fallback,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return str(session.id)
        except Exception as e:
            logger.warning(f"세션 저장 실패: {e}")
            db.rollback()
            return str(uuid.uuid4())  # 세션 저장 실패 시에도 UUID 반환
        finally:
            db.close()

    def _check_daily_limit(self, user: dict) -> None:
        """플랜별 일일 호출 제한 확인"""
        from fastapi import HTTPException
        from app.middleware.usage_tracker import get_expert_panel_daily_count

        user_id = str(user["id"])
        count = get_expert_panel_daily_count(user_id)
        plan = user.get("plan", "STARTER")
        limit = {
            "STARTER": settings.EXPERT_DAILY_LIMIT_STARTER,
            "PRO": settings.EXPERT_DAILY_LIMIT_PRO,
            "ENTERPRISE": settings.EXPERT_DAILY_LIMIT_ENTERPRISE,
        }.get(plan, settings.EXPERT_DAILY_LIMIT_STARTER)

        if limit != -1 and count >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"일일 Expert Panel 사용 한도({limit}회)를 초과했습니다. "
                       f"현재 플랜: {plan}",
            )

    def _record_usage(self, user: dict) -> None:
        """사용량 기록"""
        from app.middleware.usage_tracker import record_expert_panel_call
        record_expert_panel_call(str(user["id"]))

    def _build_cache_key(self, query: str, view: str | None, category: str | None,
                         expert_hint: ExpertType | None = None) -> str:
        """캐시 키 생성 — query + view + category + expert_hint의 MD5 해시
        expert_hint가 다르면 다른 전문가 응답이므로 반드시 키에 포함"""
        raw = f"{query}:{view or ''}:{category or ''}:{expert_hint.value if expert_hint else ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> dict | None:
        """캐시에서 조회"""
        try:
            from app.services.cache import cache_service
            result = cache_service.get(f"expert_panel_{cache_key}")
            if result:
                result["is_cache_hit"] = True
                return result
        except Exception:
            pass
        return None

    async def _save_to_cache(self, cache_key: str, result: dict) -> None:
        """캐시에 저장"""
        try:
            from app.services.cache import cache_service
            cache_service.set(f"expert_panel_{cache_key}", result, ttl=settings.EXPERT_PANEL_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Expert Panel 캐시 저장 실패: {e}")
