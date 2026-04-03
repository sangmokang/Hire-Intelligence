"""캐시 서비스 — REDIS_URL 설정 시 Redis, 미설정 시 인메모리 TTL 캐시 (싱글턴)"""
import asyncio
import functools
import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from app.config import settings

logger = logging.getLogger(__name__)

# Redis 선택적 임포트
try:
    import redis as redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class CacheService:
    """캐시 서비스.

    - REDIS_URL 설정 시: Redis sync 클라이언트 (항목별 TTL 정확 지원)
    - REDIS_URL 미설정 시: cachetools TTLCache (인메모리)
    """

    def __init__(self, maxsize: int = 1024, default_ttl: int = 1800):
        self._default_ttl = default_ttl
        self._hit_count = 0
        self._miss_count = 0

        # Redis vs 인메모리 분기
        if settings.REDIS_URL and _REDIS_AVAILABLE:
            try:
                self._redis: Optional[Any] = redis_lib.Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                self._redis.ping()  # 연결 검증
                self._memory_cache = None
                logger.info("캐시: Redis 연결 성공 (%s)", settings.REDIS_URL)
            except Exception as e:
                logger.warning("Redis 연결 실패 (%s) — 인메모리 폴백", e)
                self._redis = None
                self._memory_cache: Optional[TTLCache] = TTLCache(maxsize=maxsize, ttl=default_ttl)
        else:
            self._redis = None
            self._memory_cache = TTLCache(maxsize=maxsize, ttl=default_ttl)

    @property
    def _using_redis(self) -> bool:
        return self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회. 없거나 만료되면 None 반환."""
        try:
            if self._using_redis:
                raw = self._redis.get(key)
                if raw is None:
                    self._miss_count += 1
                    return None
                self._hit_count += 1
                return json.loads(raw)
            else:
                value = self._memory_cache.get(key)
                if value is None:
                    self._miss_count += 1
                    return None
                self._hit_count += 1
                return value
        except Exception as e:
            logger.warning("캐시 get 실패 (key=%s): %s", key, e)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장."""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        try:
            if self._using_redis:
                self._redis.setex(key, effective_ttl, json.dumps(value, default=str))
            else:
                self._memory_cache[key] = value
        except Exception as e:
            logger.warning("캐시 set 실패 (key=%s): %s", key, e)

    def invalidate(self, key: str) -> None:
        """단일 키 삭제."""
        try:
            if self._using_redis:
                self._redis.delete(key)
            else:
                self._memory_cache.pop(key, None)
        except Exception as e:
            logger.warning("캐시 invalidate 실패 (key=%s): %s", key, e)

    def invalidate_prefix(self, prefix: str) -> int:
        """프리픽스로 시작하는 모든 키 삭제. 삭제된 키 수 반환."""
        try:
            if self._using_redis:
                keys = self._redis.keys(f"{prefix}*")
                if keys:
                    self._redis.delete(*keys)
                    logger.debug("캐시 무효화: prefix=%s, 삭제된 키 수=%d", prefix, len(keys))
                return len(keys)
            else:
                keys_to_delete = [k for k in list(self._memory_cache.keys()) if str(k).startswith(prefix)]
                for k in keys_to_delete:
                    self._memory_cache.pop(k, None)
                if keys_to_delete:
                    logger.debug("캐시 무효화: prefix=%s, 삭제된 키 수=%d", prefix, len(keys_to_delete))
                return len(keys_to_delete)
        except Exception as e:
            logger.warning("캐시 invalidate_prefix 실패 (prefix=%s): %s", prefix, e)
            return 0

    def get_stats(self) -> dict:
        """캐시 통계 반환 — 관리자 모니터링용."""
        total = self._hit_count + self._miss_count
        hit_rate = round(self._hit_count / total, 4) if total > 0 else 0.0
        stats = {
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": hit_rate,
            "backend": "redis" if self._using_redis else "memory",
            "default_ttl_seconds": self._default_ttl,
        }
        if not self._using_redis and self._memory_cache is not None:
            stats["size"] = len(self._memory_cache)
            stats["maxsize"] = self._memory_cache.maxsize
        return stats


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
