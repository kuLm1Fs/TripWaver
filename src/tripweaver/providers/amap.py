"""高德地图搜索 Provider — 地理编码 + POI 周边搜索 + 路径规划"""

from typing import override

import httpx

from tripweaver.core.config import Settings
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.base import SearchProvider

# 高德 Web API 基地址
AMAP_BASE = "https://restapi.amap.com/v3"

# POI 类型映射：兴趣标签 → 高德类型码
INTEREST_TO_TYPES: dict[str, list[str]] = {
    "food": ["050000", "050100", "050200"],        # 餐饮
    "museum": ["060100", "060200"],                 # 博物馆/展览
    "history": ["060100", "110100", "090100"],      # 历史古迹
    "nature": ["110100", "110200", "110000"],       # 风景名胜
    "shopping": ["060400", "060500"],                # 购物
    "family": ["060100", "110100", "080300"],        # 亲子
    "nightlife": ["080300", "080100"],               # 休闲娱乐
}

# 默认类型：景点 + 餐饮 + 休闲
DEFAULT_TYPES = ["110100", "050000", "080300", "060100"]

# 类型码 → 中文分类名
TYPE_NAMES: dict[str, str] = {
    "05": "餐饮",
    "06": "购物/景点",
    "08": "休闲娱乐",
    "09": "生活服务",
    "11": "风景名胜",
}

# 交通方式对应的平均速度（米/分钟）
SPEED_MAP: dict[str, int] = {
    "walking": 80,    # 步行 ~5km/h
    "transit": 250,   # 公交 ~15km/h
}

# 最大搜索半径（米）
MAX_RADIUS = 10000


class AmapSearchProvider(SearchProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.amap_server_key:
            raise ValueError("AMAP_SERVER_KEY is required when SEARCH_PROVIDER=amap")
        self.key = settings.amap_server_key

    @override
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        async with httpx.AsyncClient(timeout=15) as client:
            # 1. 获取经纬度
            lng, lat, resolved_address = await self._geocode(client, request)
            if lat is None or lng is None:
                return []

            # 2. 根据交通方式和时间计算搜索半径
            radius = self._calc_radius(request.range_mode, request.range_minutes)

            # 3. 收集要搜索的 POI 类型（预设标签 + 自定义标签）
            all_interests = list(request.interests) + list(request.custom_tags)
            poi_types = self._resolve_types(all_interests)

            # 4. 周边搜索
            places = await self._search_around(client, lat, lng, poi_types, radius)

            # 5. 用目的地名填充 reason
            for p in places:
                if not p.reason:
                    p.reason = f"位于{resolved_address or request.destination}附近"

            return places

    async def plan_walking_route(
        self, waypoints: list[tuple[float, float]]
    ) -> list[dict]:
        """步行路径规划，返回各段路线坐标。

        Args:
            waypoints: 经纬度坐标列表 [(lng, lat), ...]

        Returns:
            路线段列表，每段包含 from/to 索引、坐标点、距离、耗时
        """
        if len(waypoints) < 2:
            return []

        segments = []
        async with httpx.AsyncClient(timeout=15) as client:
            for i in range(len(waypoints) - 1):
                origin = f"{waypoints[i][0]},{waypoints[i][1]}"
                destination = f"{waypoints[i+1][0]},{waypoints[i+1][1]}"

                resp = await client.get(
                    f"{AMAP_BASE}/direction/walking",
                    params={
                        "key": self.key,
                        "origin": origin,
                        "destination": destination,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "1" or not data.get("route"):
                    segments.append({
                        "from": i, "to": i + 1,
                        "points": [
                            {"lng": waypoints[i][0], "lat": waypoints[i][1]},
                            {"lng": waypoints[i+1][0], "lat": waypoints[i+1][1]},
                        ],
                        "distance": 0, "duration": 0,
                    })
                    continue

                paths = data["route"].get("paths", [])
                if not paths:
                    continue

                path = paths[0]
                points = []
                for step in path.get("steps", []):
                    polyline = step.get("polyline", "")
                    for coord in polyline.split(";"):
                        parts = coord.split(",")
                        if len(parts) == 2:
                            points.append({
                                "lng": float(parts[0]),
                                "lat": float(parts[1]),
                            })

                segments.append({
                    "from": i,
                    "to": i + 1,
                    "points": points,
                    "distance": int(path.get("distance", 0)),
                    "duration": int(path.get("duration", 0)),
                })

        return segments

    # ── 公开地理编码 ──────────────────────────────────────────

    async def geocode_address(
        self, address: str
    ) -> tuple[float | None, float | None]:
        """根据地址查询经纬度，用于 LLM 生成地点的坐标回填。"""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{AMAP_BASE}/geocode/geo",
                params={"key": self.key, "address": address, "output": "JSON"},
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "1" or not data.get("geocodes"):
                return None, None

            location = data["geocodes"][0].get("location", "")
            parts = location.split(",")
            if len(parts) != 2:
                return None, None

            return float(parts[0]), float(parts[1])

    # ── 内部地理编码 ──────────────────────────────────────────

    async def _geocode(
        self, client: httpx.AsyncClient, request: ItineraryRequest
    ) -> tuple[float | None, float | None, str | None]:
        """将地名转为经纬度。如果请求已带坐标则直接返回。"""
        if request.latitude is not None and request.longitude is not None:
            return request.longitude, request.latitude, request.address

        resp = await client.get(
            f"{AMAP_BASE}/geocode/geo",
            params={"key": self.key, "address": request.destination, "output": "JSON"},
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "1" or not data.get("geocodes"):
            return None, None, None

        geo = data["geocodes"][0]
        location = geo.get("location", "")
        parts = location.split(",")
        if len(parts) != 2:
            return None, None, None

        lng, lat = float(parts[0]), float(parts[1])
        formatted = geo.get("formatted_address")
        return lng, lat, formatted

    # ── POI 周边搜索 ─────────────────────────────────────────

    async def _search_around(
        self,
        client: httpx.AsyncClient,
        lat: float,
        lng: float,
        poi_types: list[str],
        radius: int = 3000,
    ) -> list[CandidatePlace]:
        """在经纬度周围搜索 POI，合并多种类型结果。"""
        places: list[CandidatePlace] = []
        seen_names: set[str] = set()

        for type_code in poi_types:
            resp = await client.get(
                f"{AMAP_BASE}/place/around",
                params={
                    "key": self.key,
                    "location": f"{lng},{lat}",
                    "types": type_code,
                    "radius": radius,
                    "offset": 10,
                    "page": 1,
                    "extensions": "base",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") != "1":
                continue

            for poi in data.get("pois", []):
                name = poi.get("name", "").strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)

                # 解析坐标
                loc = poi.get("location", "")
                loc_parts = loc.split(",")
                poi_lng = float(loc_parts[0]) if len(loc_parts) == 2 else None
                poi_lat = float(loc_parts[1]) if len(loc_parts) == 2 else None

                # 类型
                poi_type = poi.get("type", "")
                category = self._type_to_category(poi_type)

                # 评分/人均（高德返回的 biz_ext 可能是 dict 或 list）
                biz_ext = poi.get("biz_ext", {})
                if not isinstance(biz_ext, dict):
                    biz_ext = {}
                cost = biz_ext.get("cost", "")
                rating = biz_ext.get("rating", "")
                price = f"人均{cost}元" if cost else None
                if rating:
                    price = f"{price} · 评分{rating}" if price else f"评分{rating}"

                places.append(
                    CandidatePlace(
                        name=name,
                        category=category,
                        reason=poi.get("address", "") or f"位于目标区域周边",
                        address=poi.get("address"),
                        longitude=poi_lng,
                        latitude=poi_lat,
                        price=price,
                        business_hours=biz_ext.get("business_hours"),
                        tags=[t for t in poi.get("type", "").split(";") if t],
                    )
                )

        return places

    # ── 工具方法 ──────────────────────────────────────────────

    @staticmethod
    def _calc_radius(mode: str, minutes: int) -> int:
        """根据交通方式和时间计算搜索半径（米）。"""
        speed = SPEED_MAP.get(mode, SPEED_MAP["walking"])
        radius = speed * minutes
        return min(radius, MAX_RADIUS)

    @staticmethod
    def _resolve_types(interests: list[str]) -> list[str]:
        """将兴趣标签映射为高德 POI 类型码。"""
        types: list[str] = []
        for interest in interests:
            types.extend(INTEREST_TO_TYPES.get(interest, []))
        if not types:
            types = DEFAULT_TYPES[:]
        # 去重保序
        seen: set[str] = set()
        return [t for t in types if not (t in seen or seen.add(t))]

    @staticmethod
    def _type_to_category(type_str: str) -> str:
        """高德类型字符串 → 简短分类名。"""
        code = type_str[:2] if type_str else ""
        return TYPE_NAMES.get(code, "其他")
