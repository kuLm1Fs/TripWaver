from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest

# 三种方案风格定义
PLAN_STYLES = [
    {
        "key": "relaxed_eating",
        "title": "休闲逛吃",
        "description": "适合喜欢美食探店、轻松休闲的朋友，节奏缓慢，以吃喝为主",
        "instruction": (
            "侧重美食探店、轻松休闲，适合吃货朋友。"
            "优先安排餐饮、甜品、饮品、小吃等美食类地点，穿插轻松的休闲活动。"
            "节奏要慢，每段停留1-2小时，不要赶路。"
        ),
    },
    {
        "key": "landmark_tour",
        "title": "景点打卡",
        "description": "涵盖当地经典必去景点，适合第一次来玩的游客",
        "instruction": (
            "涵盖当地经典必去景点，适合第一次来玩的游客。"
            "优先安排地标性景点、历史文化场所、网红打卡地。"
            "路线要合理，减少重复步行，一天走完核心景点。"
        ),
    },
    {
        "key": "hidden_gems",
        "title": "小众特色",
        "description": "挖掘本地人常去的小众好去处，避开人流",
        "instruction": (
            "挖掘本地人常去的小众好去处，避开人流。"
            "优先安排小众公园、本地小店、非热门但有特色的地方。"
            "不要安排热门景区和网红店，追求独特体验。"
        ),
    },
]


def _build_candidate_text(candidates: list[CandidatePlace]) -> str:
    """构建候选地点文本。"""
    lines = []
    for i, place in enumerate(candidates, start=1):
        lines.append(f"{i}. {place.name} [{place.category}] - {place.reason}")
    return "\n".join(lines) or "未找到候选地点。"


def _build_guide_section(guide_text: str) -> str:
    """构建攻略参考段落。"""
    if not guide_text:
        return ""
    return f"\n\n参考攻略信息：\n{guide_text}"


def build_itinerary_prompt(
    request: ItineraryRequest,
    candidates: list[CandidatePlace],
    guide_text: str = "",
) -> str:
    """构建一次性生成 3 种方案的 prompt（兼容旧接口）。"""
    candidate_text = _build_candidate_text(candidates)
    all_interests = list(request.interests) + list(request.custom_tags)
    interest = ", ".join(all_interests) if all_interests else "常规观光"
    guide_section = _build_guide_section(guide_text)

    style_desc = "\n".join(
        f'{i+1}. "{s["title"]}"：{s["instruction"]}'
        for i, s in enumerate(PLAN_STYLES)
    )

    return f"""
你是一个专业的旅行行程规划助手，擅长为朋友聚会定制多样化的旅行方案。

请为 {request.destination} 生成 {request.days} 天的旅行行程，一共生成3种不同风格的方案供用户选择，分别是：
{style_desc}

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
- 每个方案对象必须包含：title、description、destination、overview、items
- items中的每一项必须包含：day、title、summary、places
- places中的每一项必须包含：name、category、reason、address、longitude、latitude、price、business_hours、tags
- 字段说明：
  - title: 方案名称，对应上面3种风格
  - description: 方案简短介绍，说明适合人群和特色
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
        "title": "休闲逛吃",
        "description": "适合喜欢美食探店、轻松休闲的朋友，节奏缓慢，以吃喝为主",
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


def build_single_day_prompt(
    request: ItineraryRequest,
    candidates: list[CandidatePlace],
    style: dict,
    day: int,
    guide_text: str = "",
) -> str:
    """构建单个方案单日行程的 prompt。

    Args:
        request: 行程请求（包含 destination、days 等）
        candidates: 候选地点
        style: PLAN_STYLES 中的一个风格定义
        day: 要生成的第几天（从1开始）
        guide_text: 攻略文本
    """
    candidate_text = _build_candidate_text(candidates)
    all_interests = list(request.interests) + list(request.custom_tags)
    interest = ", ".join(all_interests) if all_interests else "常规观光"
    guide_section = _build_guide_section(guide_text)

    return f"""
你是一个专业的旅行行程规划助手，擅长为朋友聚会定制旅行方案。

请为 {request.destination} 生成第 {day} 天的「{style["title"]}」风格行程。

风格要求：{style["instruction"]}

用户兴趣偏好：
{interest}

候选推荐地点（来自高德地图真实POI数据）：
{candidate_text}
{guide_section}

生成规则：
- 优先使用给出的候选地点，若不足可补充当地真实存在的热门地点
- 行程安排宽松合理，适合多人聚会，不要太赶
- 只返回一个 JSON 对象的 items 数组（单日），不要添加任何其他内容
- 不要在JSON前后添加解释、标题、注释或Markdown代码块
- items 中每一项必须包含：day、title、summary、places
- places 中每一项必须包含：name、category、reason、address、longitude、latitude、price、business_hours、tags
- day 固定为 {day}
- address: 地点完整地址
- longitude/latitude: 经纬度，数字类型，没有的话填null
- price: 人均消费金额/范围，字符串
- business_hours: 营业时间，字符串
- tags: 标签数组
- 如果某个字段没有合适内容，返回空字符串/[]/null，不要省略字段

请严格按照以下JSON结构返回（单个日 items 数组）：
[
    {{
        "day": {day},
        "title": "当天行程标题",
        "summary": "当天行程简述",
        "places": [
            {{
                "name": "地点名称",
                "category": "分类",
                "reason": "推荐理由",
                "address": "详细地址",
                "longitude": 120.1234,
                "latitude": 30.1234,
                "price": "人均50元",
                "business_hours": "10:00-22:00",
                "tags": ["标签1", "标签2"]
            }}
        ]
    }}
]
""".strip()


def build_single_plan_prompt(
    request,
    candidates,
    style,
    guide_text: str = "",
):
    """构建单个方案风格的专用 prompt。

    Args:
        request: 行程请求
        candidates: 候选地点
        style: PLAN_STYLES 中的一个风格定义
        guide_text: 攻略文本
    """
    candidate_text = _build_candidate_text(candidates)
    all_interests = list(request.interests) + list(request.custom_tags)
    interest = ", ".join(all_interests) if all_interests else "常规观光"
    guide_section = _build_guide_section(guide_text)

    return f"""
你是一个专业的旅行行程规划助手，擅长为朋友聚会定制旅行方案。

请为 {request.destination} 生成 {request.days} 天的「{style["title"]}」风格旅行行程。

风格要求：{style["instruction"]}

用户兴趣偏好：
{interest}

候选推荐地点（来自高德地图真实POI数据）：
{candidate_text}
{guide_section}

生成规则：
- 优先使用给出的候选地点，若不足可补充当地真实存在的热门地点
- 行程安排宽松合理，适合多人聚会，不要太赶
- 只返回一个方案的合法JSON对象，不要添加任何其他内容
- 不要在JSON前后添加解释、标题、注释或Markdown代码块
- 必须包含：title、description、destination、overview、items
- items中每一项必须包含：day、title、summary、places
- places中每一项必须包含：name、category、reason、address、longitude、latitude、price、business_hours、tags
- title 必须是「{style["title"]}」
- description: {style["description"]}
- address: 地点完整地址
- longitude/latitude: 经纬度，数字类型，没有的话填null
- price: 人均消费金额/范围，字符串
- business_hours: 营业时间，字符串
- tags: 标签数组
- 如果某个字段没有合适内容，返回空字符串/[]/null，不要省略字段
- day必须是整数，从1开始递增

请严格按照以下JSON结构返回（单个对象，不是数组）：
{{
    "title": "{style["title"]}",
    "description": "{style["description"]}",
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
                    "category": "分类",
                    "reason": "推荐理由",
                    "address": "详细地址",
                    "longitude": 120.1234,
                    "latitude": 30.1234,
                    "price": "人均50元",
                    "business_hours": "10:00-22:00",
                    "tags": ["标签1", "标签2"]
                }}
            ]
        }}
    ]
}}
""".strip()
