from statistics import quantiles
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest


def build_itinerary_prompt(
    request: ItineraryRequest,
    candidates: list[CandidatePlace],
) -> str:
    candidate_lines = []

    for index, place in enumerate(candidates, start=1):
        candidate_lines.append(f"{index}. {place.name} [{place.category}] - {place.reason}")

    candidate_text = "\n".join(candidate_lines) or "No candidate places found."

    interest = ", ".join(request.interests) if request.interests else "general sightseeing"

    return f"""
你是一个旅行计划的助手

创造一个{request.days} -天 itinerary for {request.destination}.

用户兴趣：
{interest}
候选地点：
{candidate_text}

规则：
- 把候选地点作为主要资源
- 不要创造地点除非需要
- 按日期给计划分组
- 结果要简洁
- 按照下面给出的形状，返回一个json对象：
{{
    "destination" : "{request.destination}",
    "overview" : "...",
    "items" : [
        {{
            "day" : 1,
            "title" : "...",
            "summery" : "...",
            "places" : [
                {{
                    "name" : "...",
                    "category" : "...",
                    "reason" : "..."
                }}
            ]
        }}
    ]
}}
""".strip()
