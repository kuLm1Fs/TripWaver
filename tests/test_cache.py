"""LLM 缓存服务测试"""

import pytest

from tripweaver.domain.schemas import ItineraryRequest
from tripweaver.services.cache import make_cache_key


class TestMakeCacheKey:
    """测试缓存 key 生成"""

    def test_same_params_same_key(self):
        """相同参数生成相同 key"""
        req1 = ItineraryRequest(destination="南京东路", days=1, interests=["二次元"], range_mode="walking", range_minutes=20)
        req2 = ItineraryRequest(destination="南京东路", days=1, interests=["二次元"], range_mode="walking", range_minutes=20)
        assert make_cache_key(req1) == make_cache_key(req2)

    def test_different_destination_different_key(self):
        """不同目的地生成不同 key"""
        req1 = ItineraryRequest(destination="南京东路", days=1)
        req2 = ItineraryRequest(destination="西湖", days=1)
        assert make_cache_key(req1) != make_cache_key(req2)

    def test_different_days_different_key(self):
        """不同天数生成不同 key"""
        req1 = ItineraryRequest(destination="南京东路", days=1)
        req2 = ItineraryRequest(destination="南京东路", days=2)
        assert make_cache_key(req1) != make_cache_key(req2)

    def test_interests_order_independent(self):
        """兴趣列表顺序无关"""
        req1 = ItineraryRequest(destination="南京", days=1, interests=["美食", "二次元"])
        req2 = ItineraryRequest(destination="南京", days=1, interests=["二次元", "美食"])
        assert make_cache_key(req1) == make_cache_key(req2)

    def test_different_range_mode_different_key(self):
        """不同范围模式生成不同 key"""
        req1 = ItineraryRequest(destination="南京", days=1, range_mode="walking")
        req2 = ItineraryRequest(destination="南京", days=1, range_mode="transit")
        assert make_cache_key(req1) != make_cache_key(req2)

    def test_different_range_minutes_different_key(self):
        """不同时间范围生成不同 key"""
        req1 = ItineraryRequest(destination="南京", days=1, range_minutes=20)
        req2 = ItineraryRequest(destination="南京", days=1, range_minutes=30)
        assert make_cache_key(req1) != make_cache_key(req2)

    def test_key_format(self):
        """key 以 llm_cache: 开头"""
        req = ItineraryRequest(destination="南京", days=1)
        key = make_cache_key(req)
        assert key.startswith("llm_cache:")
        assert len(key) == len("llm_cache:") + 16  # sha256[:16]

    def test_empty_interests(self):
        """空兴趣列表也能正常生成 key"""
        req = ItineraryRequest(destination="南京", days=1, interests=[])
        key = make_cache_key(req)
        assert key.startswith("llm_cache:")
