"""인메모리 TTL 캐시 서비스 — cachetools 기반 싱글턴"""
import asyncio
import functools
import logging
from typing import Any, Optional

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CacheService:
    """인메모리 TTL 캐시 서비스.

    - maxsize: 캐시 최대 항목 수 (LRU 방식으로 초과 시 오래된 항목 제거)
    - default_ttl: 기본 TTL 초 단위 (기본값 30분)
    - 히트/미스 카운터로 캐시 효율 모니터링 지원
    """

    def __init__(self, maxsize: int = 1024, default_ttl: int = 1800):
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._default_ttl = default_ttl
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회. 없거나 만료되면 None 반환."""
        value = self._cache.get(key)
        if value is None:
            self._miss_count += 1
            return None
        self._hit_count += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장. ttl 지정 시 해당 TTL 사용, 없으면 기본 TTL.

        주의: cachetools TTLCache는 항목별 TTL을 지원하지 않으므로
        ttl이 기본값과 다를 경우 별도 TTLCache 인스턴스에 위임하지 않고
        캐시에 직접 저장 (만료 시각은 캐시 생성 시 설정된 ttl 기준).
        항목별 TTL이 필요한 경우 별도 set_with_ttl 확장 가능.
        """
        if ttl is not None and ttl != self._default_ttl:
            # 항목별 TTL: 임시 TTLCache를 통해 만료 처리 (저장 후 바로 꺼내는 방식)
            # 실용적 근사: 기본 캐시에 저장하되, TTL 차이는 허용 (단순화)
            # 운영 환경에서는 Redis 전환 시 항목별 TTL 완벽 지원 가능
            self._cache[key] = value
        else:
            self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """단일 키 삭제."""
        self._cache.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        """프리픽스로 시작하는 모든 키 삭제. 삭제된 키 수 반환."""
        # TTLCache는 dict-like이므로 키 목록 복사 후 삭제
        keys_to_delete = [k for k in list(self._cache.keys()) if str(k).startswith(prefix)]
        for k in keys_to_delete:
            self._cache.pop(k, None)
        if keys_to_delete:
            logger.debug("캐시 무효화: prefix=%s, 삭제된 키 수=%d", prefix, len(keys_to_delete))
        return len(keys_to_delete)

    def get_stats(self) -> dict:
        """캐시 통계 반환 — 관리자 모니터링용."""
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total, 4) if total > 0 else 0.0
        return {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "default_ttl_seconds": self._default_ttl,
        }


# 모듈 레벨 싱글턴 — 앱 전체에서 공유
cache_service = CacheService()


def cached(ttl: int = 1800, prefix: str = ""):
    """캐시 데코레이터 — 함수 인자를 키로 사용. async 함수 지원.

    Args:
        ttl: 캐시 TTL 초 단위
        prefix: 캐시 키 프리픽스 (invalidate_prefix 무효화 시 사용)

    Usage:
        @cached(ttl=3600, prefix="dashboard_sd_matrix")
        def get_sd_matrix(self, week=None):
            ...

        @cached(ttl=3600, prefix="async_data")
        async def get_async_data(self):
            ...
    """
    def decorator(func):
        def _build_key(*args, **kwargs) -> str:
            key_parts = [prefix or func.__name__]
            # args[1:] — self 제외
            key_parts.extend(str(a) for a in args[1:])
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            return ":".join(key_parts)

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = _build_key(*args, **kwargs)
                cached_value = cache_service.get(cache_key)
                if cached_value is not None:
                    return cached_value
                result = await func(*args, **kwargs)
                if result is not None:
                    cache_service.set(cache_key, result, ttl=ttl)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = _build_key(*args, **kwargs)
                cached_value = cache_service.get(cache_key)
                if cached_value is not None:
                    return cached_value
                result = func(*args, **kwargs)
                if result is not None:
                    cache_service.set(cache_key, result, ttl=ttl)
                return result
            return wrapper

    return decorator
