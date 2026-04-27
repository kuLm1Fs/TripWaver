from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest


def build_itinerary_prompt(
    request: ItineraryRequest,
    candidates: list[CandidatePlace],
    guide_text: str = "",
) -> str:
    candidate_lines = []

    for index, place in enumerate(candidates, start=1):
        candidate_lines.append(f"{index}. {place.name} [{place.category}] - {place.reason}")

    candidate_text = "\n".join(candidate_lines) or "未找到候选地点。"

    all_interests = list(request.interests) + list(request.custom_tags)
    interest = ", ".join(all_interests) if all_interests else "常规观光"

    guide_section = ""
    if guide_text:
        guide_section = f"""

参考攻略信息：
{guide_text}"""

    return f"""
你是一个专业的旅行行程规划助手，擅长为朋友聚会定制多样化的旅行方案。

请为 {request.destination} 生成 {request.days} 天的旅行行程，一共生成3种不同风格的方案供用户选择，分别是：
1. "休闲逛吃"：侧重美食探店、轻松休闲，适合吃货朋友
2. "景点打卡"：涵盖当地经典必去景点，适合第一次来玩的游客
3. "小众特色"：挖掘本地人常去的小众好去处，避开人流

用户兴趣偏好：
{interest}

候选推荐地点（来自高德地图真实POI数据）：
{candidate_text}
{guide_section}

生成规则：
- 优先使用给出的候选地点作为主要信息来源，若候选地点不足可补充当地真实存在的热门地点
- 3种方案风格差异要明显，不要同质化
- 每个方案独立完整，包含自己的overview和按天的行程安排
- 每天的行程安排宽松合理，适合多人聚会的节奏，不要安排太赶
- 只能返回合法JSON，不要添加任何其他内容
- 不要在JSON前后添加解释、标题、注释或Markdown代码块
- 顶层结构为数组，包含3个方案对象
- 每个方案对象必须包含：plan_name、plan_desc、destination、overview、items
- items中的每一项必须包含：day、title、summary、places
- places中的每一项必须包含：name、category、reason、address、longitude、latitude、price、business_hours、tags
- 字段说明：
  - plan_name: 方案名称，对应上面3种风格
  - plan_desc: 方案简短介绍，说明适合人群和特色
  - address: 地点完整地址
  - longitude/latitude: 经纬度，数字类型，没有的话填null
  - price: 人均消费金额/范围，字符串
  - business_hours: 营业时间，字符串
  - tags: 标签数组，比如["网红店","老字号","适合拍照"]
- 如果某个字段没有合适内容，返回空字符串/[]/null，不要省略字段
- day必须是整数，并且从1开始递增

请严格按照以下JSON结构返回：
[
    {{
        "plan_name": "休闲逛吃",
        "plan_desc": "适合喜欢美食探店、轻松休闲的朋友，节奏缓慢，以吃喝为主",
        "destination": "{request.destination}",
        "overview": "...",
        "items": [
            {{
                "day": 1,
                "title": "第一天行程标题",
                "summary": "当天行程简述",
                "places": [
                    {{
                        "name": "地点名称",
                        "category": "分类，比如美食/景点/娱乐",
                        "reason": "推荐理由",
                        "address": "详细地址",
                        "longitude": 120.1234,
                        "latitude": 30.1234,
                        "price": "人均50元",
                        "business_hours": "10:00-22:00",
                        "tags": ["美食", "老字号", "适合拍照"]
                    }}
                ]
            }}
        ]
    }}
]
""".strip()
