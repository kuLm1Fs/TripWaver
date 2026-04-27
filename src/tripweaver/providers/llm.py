import asyncio
import json
from typing import override

import structlog
from volcenginesdkarkruntime import Ark

from tripweaver.core.config import Settings
from tripweaver.domain.schemas import (
    CandidatePlace,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
)
from tripweaver.providers.base import LLMProvider
from tripweaver.providers.llm_prompt import build_itinerary_prompt

logger = structlog.get_logger(__name__)


class MockLLMProvider(LLMProvider):
    @override
    async def generate_itinerary(
        self, request: ItineraryRequest, candidates: list[CandidatePlace],
        guide_text: str = "",
    ) -> ItineraryResponse:
        items = []

        for day in range(1, request.days + 1):
            items.append(
                ItineraryItem(
                    day=day,
                    title=f"Day {day} in {request.destination}",
                    summary="A simple mock itinerary day",
                    places=candidates,
                )
            )
        # 生成模拟的3个方案
        plan_options = [
            {
                "title": "休闲逛吃",
                "description": "适合喜欢美食探店、轻松休闲的朋友",
                "destination": request.destination,
                "overview": f"休闲吃逛{request.days}天行程",
                "items": [item.model_dump() for item in items]
            },
            {
                "title": "景点打卡",
                "description": "涵盖当地经典必去景点，适合第一次来玩的游客",
                "destination": request.destination,
                "overview": f"经典景点{request.days}天打卡行程",
                "items": [item.model_dump() for item in items]
            },
            {
                "title": "小众特色",
                "description": "挖掘本地人常去的小众好去处，避开人流",
                "destination": request.destination,
                "overview": f"小众特色{request.days}天深度行程",
                "items": [item.model_dump() for item in items]
            }
        ]
        return ItineraryResponse(
            destination=request.destination,
            overview=f"A {request.days}-day trip in {request.destination}",
            items=items,
            plan_options=plan_options
        )


class ARKLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = Ark(api_key=settings.ark_api_key, base_url=settings.ark_base_url)

    @override
    async def generate_itinerary(
        self, request: ItineraryRequest, candidates: list[CandidatePlace],
        guide_text: str = "",
    ) -> ItineraryResponse:
        if not self.settings.ark_api_key:
            raise ValueError("ARK_API_KEY is required when LLM_PROVIDER = ark")

        prompt = build_itinerary_prompt(request, candidates, guide_text)

        try:
            # 增加重试机制，最多重试2次
            for retry in range(3):
                try:
                    response = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.settings.ark_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        timeout=300, # 5分钟超时，足够长
                        max_tokens=4096, # 增加输出长度限制，避免截断
                    )
                    text = response.choices[0].message.content.strip()
                    logger.info("LLM生成完成", text_length=len(text), retry_times=retry)
                    break
                except Exception as e:
                    if retry < 2:
                        logger.warning("LLM调用失败，正在重试", error=str(e), retry_times=retry+1)
                        await asyncio.sleep(2)
                    else:
                        raise e
            
        except Exception as e:
            logger.error("LLM调用最终失败", error=str(e))
            raise RuntimeError(f"行程生成失败：{str(e)}") from e

        # 解析 JSON
        data = json.loads(text)

        # 适配返回数组或者单个对象的情况，同时统一字段名和前端匹配
        if isinstance(data, list):
            # 多方案返回，取第一个作为默认方案
            plan_options = []
            for plan in data:
                # 字段名适配：plan_name->title, plan_desc->description
                adapted_plan = {
                    "title": plan.get("plan_name") or plan.get("title", "未命名方案"),
                    "description": plan.get("plan_desc") or plan.get("description", ""),
                    "items": plan.get("items", []),
                    "overview": plan.get("overview", "")
                }
                plan_options.append(adapted_plan)
            main_plan = plan_options[0] if plan_options else {}
        else:
            # 兼容单个方案返回
            adapted_plan = {
                "title": data.get("plan_name") or data.get("title", "未命名方案"),
                "description": data.get("plan_desc") or data.get("description", ""),
                "items": data.get("items", []),
                "overview": data.get("overview", "")
            }
            plan_options = [adapted_plan]
            main_plan = adapted_plan
        
        # 解析主方案
        items = []
        for item in main_plan.get("items", []):
            places = []

            for place in item.get("places", []):
                places.append(
                    CandidatePlace(
                        name=place.get("name", "Unknown place"),
                        category=place.get("category", "unknown"),
                        reason=place.get("reason", ""),
                        address=place.get("address", ""),
                        longitude=place.get("longitude"),
                        latitude=place.get("latitude"),
                        price=place.get("price", ""),
                        business_hours=place.get("business_hours", ""),
                        tags=place.get("tags", []),
                    )
                )

            items.append(
                ItineraryItem(
                    day=item.get("day", 1),
                    title=item.get("title", "Untitled"),
                    summary=item.get("summary", ""),
                    places=places,
                )
            )
        return ItineraryResponse(
            destination=main_plan.get("destination", request.destination),
            overview=main_plan.get("overview", ""),
            items=items,
            plan_options=plan_options
        )
