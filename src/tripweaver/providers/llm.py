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
from tripweaver.providers.llm_prompt import (
    PLAN_STYLES,
    build_itinerary_prompt,
    build_single_plan_prompt,
)

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

        # 模拟并行生成：3 个方案
        plan_options = []
        for style in PLAN_STYLES:
            plan_options.append({
                "title": style["title"],
                "description": style["description"],
                "destination": request.destination,
                "overview": f"{style['title']}{request.days}天行程",
                "items": [item.model_dump() for item in items],
            })

        return ItineraryResponse(
            destination=request.destination,
            overview=f"A {request.days}-day trip in {request.destination}",
            items=items,
            plan_options=plan_options,
        )


class ARKLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = Ark(api_key=settings.ark_api_key, base_url=settings.ark_base_url)

    async def _call_llm(self, prompt: str, label: str = "") -> str:
        """调用 LLM 并返回文本结果，带重试机制。"""
        for retry in range(3):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.settings.ark_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    timeout=300,
                    max_tokens=4096,
                )
                text = response.choices[0].message.content.strip()
                logger.info(
                    "LLM生成完成",
                    label=label,
                    text_length=len(text),
                    retry_times=retry,
                )
                return text
            except Exception as e:
                if retry < 2:
                    logger.warning(
                        "LLM调用失败，正在重试",
                        label=label,
                        error=str(e),
                        retry_times=retry + 1,
                    )
                    await asyncio.sleep(2)
                else:
                    raise

    async def _generate_single_plan(
        self,
        request: ItineraryRequest,
        candidates: list[CandidatePlace],
        style: dict,
        guide_text: str = "",
    ) -> dict | None:
        """为单个风格生成一个方案，返回 dict 或 None（失败时）。"""
        label = style["title"]
        prompt = build_single_plan_prompt(request, candidates, style, guide_text)
        try:
            text = await self._call_llm(prompt, label=label)
            data = json.loads(text)
            # LLM 可能返回数组或单个对象
            if isinstance(data, list):
                plan = data[0] if data else {}
            else:
                plan = data
            # 字段名适配
            return {
                "title": plan.get("title", style["title"]),
                "description": plan.get("description", style["description"]),
                "destination": plan.get("destination", request.destination),
                "overview": plan.get("overview", ""),
                "items": plan.get("items", []),
            }
        except Exception as e:
            logger.error("方案生成失败", style=label, error=str(e))
            return None

    @override
    async def generate_itinerary(
        self, request: ItineraryRequest, candidates: list[CandidatePlace],
        guide_text: str = "",
    ) -> ItineraryResponse:
        if not self.settings.ark_api_key:
            raise ValueError("ARK_API_KEY is required when LLM_PROVIDER = ark")

        # 并行生成 3 个方案
        logger.info("开始并行生成3个方案")
        tasks = [
            self._generate_single_plan(request, candidates, style, guide_text)
            for style in PLAN_STYLES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集成功的方案
        plan_options = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("方案生成异常", style=PLAN_STYLES[i]["title"], error=str(result))
            elif result is not None:
                plan_options.append(result)

        if not plan_options:
            raise RuntimeError("所有方案生成失败")

        logger.info(
            "并行生成完成",
            success=len(plan_options),
            total=len(PLAN_STYLES),
        )

        # 主方案取第一个成功的
        main_plan = plan_options[0]
        items = self._parse_items(main_plan.get("items", []))

        return ItineraryResponse(
            destination=main_plan.get("destination", request.destination),
            overview=main_plan.get("overview", ""),
            items=items,
            plan_options=plan_options,
        )

    @staticmethod
    def _parse_items(raw_items: list[dict]) -> list[ItineraryItem]:
        """解析 items JSON 为 ItineraryItem 列表。"""
        items = []
        for item in raw_items:
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
        return items
