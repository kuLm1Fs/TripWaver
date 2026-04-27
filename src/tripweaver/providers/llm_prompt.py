from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest


def build_itinerary_prompt(
    request: ItineraryRequest,
    candidates: list[CandidatePlace],
) -> str:
    candidate_lines = []

    for index, place in enumerate(candidates, start=1):
        candidate_lines.append(f"{index}. {place.name} [{place.category}] - {place.reason}")

    candidate_text = "\n".join(candidate_lines) or "未找到候选地点。"

    interest = ", ".join(request.interests) if request.interests else "常规观光"

    return f"""
你是一个旅行行程规划助手。

请为 {request.destination} 生成一个 {request.days} 天的旅行 itinerary。

用户兴趣：
{interest}

候选地点：
{candidate_text}

规则：
- 优先使用候选地点作为主要信息来源。
- 除非 absolutely necessary，否则不要凭空虚构地点。
- 行程必须按天分组。
- 输出内容保持简洁、清晰、可执行。
- 只能返回合法 JSON。
- 不要在 JSON 前后添加解释、标题、注释或 Markdown 代码块。
- 顶层对象必须包含：destination、overview、items。
- items 中的每一项必须包含：day、title、summary、places。
- places 中的每一项必须包含：name、category、reason。
- 如果某个字段没有合适内容，返回空字符串，不要省略字段。
- day 必须是整数，并且从 1 开始递增。
- places 必须是数组，即使为空也要返回 []。
- 请严格按照下面的 JSON 结构返回：
{{
    "destination": "{request.destination}",
    "overview": "...",
    "items": [
        {{
            "day": 1,
            "title": "...",
            "summary": "...",
            "places": [
                {{
                    "name": "...",
                    "category": "...",
                    "reason": "..."
                }}
            ]
        }}
    ]
}}
""".strip()
