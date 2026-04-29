# 迭代 010：行程编辑/修改接口

## 背景

用户生成行程后无法修改，只能删除重建。用户无法：
- 手动调整某一天的地点
- 更新行程概览
- 重新生成某一天（用新兴趣偏好）

## 新增接口

### 1. `PATCH /api/v1/itineraries/{id}` — 更新行程概览

**请求：**
```json
{ "overview": "新的行程简介" }
```

**响应：** `{ "success": true }`

**权限：** 仅创建者可操作

---

### 2. `PUT /api/v1/itineraries/{id}/days/{day}/places` — 更新某天地点

**请求：**
```json
{
  "plan_index": 0,
  "day": 2,
  "title": "第二天：美食之旅",
  "summary": "全天以美食为主",
  "places": [
    { "name": "外婆家", "category": "美食", "reason": "推荐", "address": "...", "longitude": 120.1, "latitude": 30.2 }
  ]
}
```

**响应：** `{ "success": true }`

**说明：** 替换指定方案（plan_index）下指定 day 的地点列表

---

### 3. `POST /api/v1/itineraries/{id}/regenerate-day` — 重新生成某天

**请求：**
```json
{
  "plan_index": 0,
  "day": 2,
  "interests": ["美食", "夜景"]
}
```

**响应：**
```json
{
  "success": true,
  "day": 2,
  "items": [{ "day": 2, "title": "...", "places": [...] }]
}
```

**说明：** 保留原方案风格，重新搜索并生成指定天

## 新增 Schema

| Schema | 文件 | 说明 |
|--------|------|------|
| `UpdateItineraryRequest` | `domain/schemas/base.py` | 更新概览请求 |
| `UpdateDayPlacesRequest` | `domain/schemas/base.py` | 更新地点请求 |
| `RegenerateDayRequest` | `domain/schemas/base.py` | 重新生成请求 |

## 新增 Prompt

`build_single_day_prompt()` — 生成单日行程 prompt，支持指定 day 参数

## 修改文件

| 文件 | 改动 |
|------|------|
| `domain/schemas/base.py` | 新增 3 个编辑相关 schema |
| `providers/llm_prompt.py` | 新增 `build_single_day_prompt()` |
| `api/routes/itineraries.py` | 新增 3 个编辑接口 |

## 验证

1. `uv run pytest` — 全部通过 ✅
