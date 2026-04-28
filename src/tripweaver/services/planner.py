"""行程规划服务 — 串联搜索、攻略、LLM 生成"""

import asyncio
from time import perf_counter

import structlog

from tripweaver.core.logging import bind_metric
from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.providers.base import LLMProvider, SearchProvider, SupplementSearchProvider
from tripweaver.services.cache import get_cached, incr_stats, set_cached

logger = structlog.get_logger(__name__)


class PlannerService:
    def __init__(
        self,
        search_provider: SearchProvider,
        llm_provider: LLMProvider,
        supplement_provider: SupplementSearchProvider | None = None,
        amap_provider: object | None = None,
    ) -> None:
        self.search_provider = search_provider
        self.llm_provider = llm_provider
        self.supplement_provider = supplement_provider
        self.amap_provider = amap_provider

    async def plan(self, request: ItineraryRequest) -> ItineraryResponse:
        from tripweaver.services.cache import make_cache_key

        cache_key = make_cache_key(request)
        cached = await get_cached(cache_key)
        if cached:
            logger.info("llm_cache_hit", key=cache_key)
            await incr_stats(hits=True)
            bind_metric(cache_hit=True, llm_cached=True)
            return cached

        await incr_stats(hits=False)
        bind_metric(cache_hit=False, llm_cached=False)

        t0 = perf_counter()
        logger.info("开始搜索POI", destination=request.destination, range_mode=request.range_mode)
        candidates = await self.search_provider.search_places(request)
        search_ms = (perf_counter() - t0) * 1000
        logger.info("poi_searched", destination=request.destination, candidates=len(candidates), duration_ms=round(search_ms, 2))

        t1 = perf_counter()
        logger.info("开始LLM生成行程")
        itinerary = await self.llm_provider.generate_itinerary(request, candidates)
        llm_ms = (perf_counter() - t1) * 1000
        logger.info(
            "llm_generated",
            plans=len(itinerary.plan_options),
            days=len(itinerary.items),
            duration_ms=round(llm_ms, 2),
        )

        # 回填坐标
        await self._backfill_coordinates(itinerary, candidates)

        # 写入缓存
        await set_cached(cache_key, itinerary)
        bind_metric(llm_duration_ms=round(llm_ms, 2), search_duration_ms=round(search_ms, 2))

        return itinerary

    async def _backfill_coordinates(
        self, response: ItineraryResponse, candidates: list
    ) -> None:
        """为 LLM 生成的地点回填经纬度坐标。

        策略：
        1. 精确匹配候选 POI 名称
        2. 模糊匹配（名称互相包含）
        3. 调用高德地理编码 API 根据地址查询

        注意：同一地名可能出现在 response.items（Pydantic 对象）和
        plan_options（dict）两处，需要都设置坐标，不做去重。
        """
        # 建立候选 POI 索引（名称 → (lng, lat)）
        candidate_map: dict[str, tuple[float, float]] = {}
        for c in candidates:
            if c.longitude is not None and c.latitude is not None:
                candidate_map[c.name] = (c.longitude, c.latitude)

        # 坐标缓存：名称 → (lng, lat)，避免重复地理编码
        coord_cache: dict[str, tuple[float, float]] = {}

        # 收集所有需要回填的 place（不去重，每个实例都要设置）
        all_places: list[tuple[object, str, str]] = []  # (place_obj, name, address)

        def collect_places(items: list) -> None:
            for item in items:
                places = item.places if hasattr(item, "places") else item.get("places", [])
                for place in places:
                    is_model = hasattr(place, "name")
                    name = place.name if is_model else place.get("name", "")
                    lng = place.longitude if is_model else place.get("longitude")
                    lat = place.latitude if is_model else place.get("latitude")
                    address = place.address if is_model else place.get("address", "")
                    if name and lng is None and lat is None:
                        all_places.append((place, name, address or ""))

        collect_places(response.items)
        for plan in response.plan_options:
            collect_places(plan.get("items", []) if isinstance(plan, dict) else [])

        if not all_places:
            return

        logger.info("开始坐标回填", places_count=len(all_places))

        # 阶段 1：名称匹配
        geocode_needed: dict[str, list[tuple[object, str]]] = {}  # address → [(place_obj, name)]
        matched = 0
        for place_obj, name, address in all_places:
            # 先查缓存
            if name in coord_cache:
                self._set_place_coord(place_obj, *coord_cache[name])
                matched += 1
                continue
            # 再查候选
            coord = self._match_candidate(name, candidate_map)
            if coord:
                coord_cache[name] = coord
                self._set_place_coord(place_obj, coord[0], coord[1])
                matched += 1
            else:
                geocode_needed.setdefault(address, []).append((place_obj, name))

        logger.info("名称匹配完成", matched=matched, need_geocode=len(geocode_needed))

        # 阶段 2：地理编码（仅当有 amap provider 时）
        if geocode_needed and self.amap_provider is not None:
            if hasattr(self.amap_provider, "geocode_address"):
                geocoded = await self._geocode_places(geocode_needed)
                logger.info("地理编码完成", geocoded=geocoded)

    @staticmethod
    def _set_place_coord(place: object, lng: float, lat: float) -> None:
        """设置地点坐标，兼容 Pydantic model 和 dict。"""
        if hasattr(place, "longitude"):
            place.longitude = lng
            place.latitude = lat
        elif isinstance(place, dict):
            place["longitude"] = lng
            place["latitude"] = lat

    @staticmethod
    def _match_candidate(
        name: str, candidate_map: dict[str, tuple[float, float]]
    ) -> tuple[float, float] | None:
        """尝试从候选 POI 中匹配坐标。"""
        # 精确匹配
        if name in candidate_map:
            return candidate_map[name]

        # 模糊匹配：候选名包含在 LLM 地名中，或反过来
        for cand_name, coord in candidate_map.items():
            if cand_name in name or name in cand_name:
                return coord

        return None

    async def _geocode_places(
        self, geocode_needed: dict[str, list[tuple[object, str]]]
    ) -> int:
        """并发地理编码，限制并发数避免触发限流。

        Args:
            geocode_needed: {address: [(place_obj, name), ...]}
        """
        assert self.amap_provider is not None

        semaphore = asyncio.Semaphore(3)
        geocoded_count = 0

        async def geocode_one(address: str, place_list: list[tuple[object, str]]) -> None:
            nonlocal geocoded_count
            if not address:
                return
            async with semaphore:
                try:
                    lng, lat = await self.amap_provider.geocode_address(address)
                    if lng is not None and lat is not None:
                        for place_obj, _name in place_list:
                            self._set_place_coord(place_obj, lng, lat)
                        geocoded_count += len(place_list)
                except Exception as e:
                    logger.warning("地理编码失败", address=address, error=str(e))

        await asyncio.gather(
            *(geocode_one(addr, places) for addr, places in geocode_needed.items())
        )
        return geocoded_count
