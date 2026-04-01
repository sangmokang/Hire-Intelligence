"""
Sprint 5 캐시 서비스 단위 + 통합 테스트
- CacheService: get, set, invalidate, invalidate_prefix, get_stats, TTL 만료
"""
import time
import pytest
from app.services.cache import CacheService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cache():
    """테스트용 독립 CacheService 인스턴스 (싱글턴 오염 방지)"""
    return CacheService(maxsize=256, default_ttl=3600)


# ---------------------------------------------------------------------------
# 테스트
# ---------------------------------------------------------------------------

class TestCacheHitMiss:
    def test_cache_hit(self, cache: CacheService):
        """set 후 get에서 같은 값 반환 (캐시 히트)"""
        cache.set("key_hit", {"result": 42})
        value = cache.get("key_hit")
        assert value == {"result": 42}, "캐시 히트: set한 값과 동일해야 함"

    def test_cache_miss(self, cache: CacheService):
        """존재하지 않는 키 get → None 반환 (캐시 미스)"""
        value = cache.get("nonexistent_key_xyz")
        assert value is None, "캐시 미스: None을 반환해야 함"

    def test_cache_hit_increments_hit_count(self, cache: CacheService):
        """캐시 히트 시 hit_count 증가 확인"""
        cache.set("count_key", "value")
        cache.get("count_key")
        stats = cache.get_stats()
        assert stats["hit_count"] >= 1, "캐시 히트 카운터가 증가해야 함"

    def test_cache_miss_increments_miss_count(self, cache: CacheService):
        """캐시 미스 시 miss_count 증가 확인"""
        cache.get("missing_key_abc")
        stats = cache.get_stats()
        assert stats["miss_count"] >= 1, "캐시 미스 카운터가 증가해야 함"


class TestCacheTTL:
    def test_ttl_expiry(self):
        """TTL 1초 캐시: 2초 대기 후 get → None"""
        short_ttl_cache = CacheService(maxsize=64, default_ttl=1)
        short_ttl_cache.set("ttl_key", "will_expire")
        # 만료 전 확인
        assert short_ttl_cache.get("ttl_key") == "will_expire", "만료 전에는 값이 있어야 함"
        time.sleep(2)
        # 만료 후 확인
        value = short_ttl_cache.get("ttl_key")
        assert value is None, "TTL 만료 후 None을 반환해야 함"


class TestCacheInvalidate:
    def test_invalidate_single_key(self, cache: CacheService):
        """invalidate: set 후 invalidate, get에서 None"""
        cache.set("del_key", "to_delete")
        assert cache.get("del_key") == "to_delete"
        cache.invalidate("del_key")
        assert cache.get("del_key") is None, "invalidate 후 None을 반환해야 함"

    def test_invalidate_prefix(self, cache: CacheService):
        """invalidate_prefix: 여러 키 set 후 프리픽스로 일괄 삭제"""
        cache.set("prefix_a:1", "val1")
        cache.set("prefix_a:2", "val2")
        cache.set("prefix_b:1", "other")

        deleted_count = cache.invalidate_prefix("prefix_a:")

        assert deleted_count == 2, f"2개 키가 삭제돼야 함, 실제: {deleted_count}"
        assert cache.get("prefix_a:1") is None, "prefix_a:1 삭제됨"
        assert cache.get("prefix_a:2") is None, "prefix_a:2 삭제됨"
        assert cache.get("prefix_b:1") == "other", "다른 프리픽스 키는 유지돼야 함"


class TestCacheStats:
    def test_get_stats_fields(self, cache: CacheService):
        """get_stats → hit_count, miss_count, size, hit_rate 필드 확인"""
        cache.set("stats_key", "stats_val")
        cache.get("stats_key")   # hit
        cache.get("no_such")     # miss

        stats = cache.get_stats()

        assert "hit_count" in stats, "hit_count 필드 필요"
        assert "miss_count" in stats, "miss_count 필드 필요"
        assert "hit_rate" in stats, "hit_rate 필드 필요"
        assert "size" in stats, "size 필드 필요"
        assert stats["hit_count"] >= 1
        assert stats["miss_count"] >= 1
        assert 0.0 <= stats["hit_rate"] <= 1.0, "hit_rate는 0~1 사이여야 함"
        assert stats["size"] >= 1
