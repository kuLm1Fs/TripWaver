# TripWeaver API 接口文档

**Base URL:** `/api/v1`
**认证方式:** Bearer Token (JWT)
**Token 获取:** 通过登录接口获取，放在请求头 `Authorization: Bearer <token>`

---

## 1. 健康检查

### `GET /health`

无需认证。

**响应:**
```json
{ "status": "ok" }
```

---

## 2. 认证模块 `/api/v1/auth`

### 2.1 发送验证码

**`POST /api/v1/auth/send-code`**

无需认证。开发环境固定返回验证码 `123456`。

**请求体:**
```json
{
  "phone": "13800138000"    // 手机号，正则 ^1[3-9]\d{9}$
}
```

**响应:**
```json
{
  "success": true,
  "message": "验证码已发送，测试环境固定验证码：123456"
}
```

### 2.2 手机号验证码登录

**`POST /api/v1/auth/login`**

无需认证。用户不存在时自动创建。

**请求体:**
```json
{
  "phone": "13800138000",   // 手机号
  "code": "123456"          // 6位验证码
}
```

**响应:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "nickname": "用户8000",
  "avatar": null
}
```

**错误:**
- `400` — 验证码错误

---

## 3. 行程规划 `/api/v1/itineraries`

> 以下接口均需认证 (`Authorization: Bearer <token>`)

### 3.1 生成行程规划

**`POST /api/v1/itineraries/plan`**

**请求体:**
```json
{
  "destination": "杭州",                    // 必填，目的地
  "days": 3,                                // 天数，1~30，默认1
  "interests": ["美食", "自然风光"],          // 兴趣标签列表
  "latitude": 30.2741,                      // 可选，纬度
  "longitude": 120.1551,                    // 可选，经度
  "address": "浙江省杭州市"                   // 可选，标准地址
}
```

**响应:**
```json
{
  "itinerary_id": 1,
  "destination": "杭州",
  "overview": "杭州三日游行程概览...",
  "items": [
    {
      "day": 1,
      "title": "西湖经典一日游",
      "summary": "...",
      "places": [
        {
          "name": "西湖",
          "category": "景点",
          "reason": "杭州标志性景点",
          "address": "杭州市西湖区",
          "longitude": 120.1487,
          "latitude": 30.2426,
          "price": "免费",
          "business_hours": "全天开放",
          "tags": ["世界遗产", "5A景区"]
        }
      ]
    }
  ],
  "plan_options": [
    {
      "title": "经典路线",
      "description": "...",
      "items": [...]
    }
  ]
}
```

### 3.2 获取我的行程列表

**`GET /api/v1/itineraries`**

**响应:**
```json
[
  {
    "id": 1,
    "destination": "杭州",
    "days": 3,
    "interests": ["美食", "自然风光"],
    "is_locked": false,
    "created_at": "2026-04-27T10:00:00"
  }
]
```

### 3.3 获取行程详情

**`GET /api/v1/itineraries/{itinerary_id}`**

**路径参数:**
- `itinerary_id` — 行程ID

**响应:**
```json
{
  "itinerary_id": 1,
  "destination": "杭州",
  "days": 3,
  "interests": ["美食"],
  "overview": "...",
  "items": [...],
  "plan_options": [...],
  "is_locked": false,
  "locked_at": null,
  "final_plan_index": null,
  "creator_id": 1,
  "is_creator": true,
  "members": [
    {
      "user_id": 1,
      "nickname": "用户8000",
      "avatar": null,
      "joined_at": "2026-04-27T10:00:00"
    }
  ],
  "vote_stats": [
    { "plan_index": 0, "count": 3 },
    { "plan_index": 1, "count": 1 }
  ],
  "current_user_vote": 0,
  "created_at": "2026-04-27T10:00:00",
  "updated_at": "2026-04-27T10:00:00"
}
```

**错误:**
- `404` — 行程不存在

---

## 4. 行程扩展功能 `/api/v1/itinerary`

> 以下接口均需认证

### 4.1 生成分享链接

**`POST /api/v1/itinerary/share`**

仅行程创建者可操作。

**请求体:**
```json
{
  "itinerary_id": 1,      // 行程ID
  "expire_days": 7         // 有效期天数，默认7天，0表示永久
}
```

**响应:**
```json
{
  "share_id": "a1b2c3d4",
  "share_url": "/share/a1b2c3d4",
  "expire_at": "2026-05-04T10:00:00",
  "created_at": "2026-04-27T10:00:00"
}
```

**错误:**
- `404` — 行程不存在或无权限

### 4.2 通过分享链接获取行程

**`GET /api/v1/itinerary/share/{share_id}`**

访问后自动加入行程群组。

**路径参数:**
- `share_id` — 分享短链接ID

**响应:** 同 3.3 获取行程详情。

**错误:**
- `404` — 分享链接不存在或已过期

### 4.3 行程方案投票

**`POST /api/v1/itinerary/vote`**

每个用户对同一行程只能投一次票。行程锁定后不可投票。

**请求体:**
```json
{
  "itinerary_id": 1,       // 行程ID
  "plan_index": 0           // 方案索引，>= 0
}
```

**响应:**
```json
{
  "success": true,
  "message": "投票成功",
  "itinerary_id": 1,
  "plan_index": 0,
  "vote_stats": [
    { "plan_index": 0, "count": 3 },
    { "plan_index": 1, "count": 1 }
  ]
}
```

**错误:**
- `404` — 行程不存在
- `400` — 行程已锁定 / 已投过票

### 4.4 锁定/解锁行程

**`POST /api/v1/itinerary/lock`**

仅行程创建者可操作。

**Query 参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `itinerary_id` | int | 是 | 行程ID |
| `plan_index` | int | 否 | 锁定时确认的方案索引 |
| `action` | string | 否 | `lock`(默认) 或 `unlock` |

**响应:**
```json
{
  "success": true,
  "message": "行程锁定成功",
  "is_locked": true,
  "final_plan_index": 0
}
```

**错误:**
- `404` — 行程不存在或无权限
- `400` — 无效操作

---

## 数据模型总览

### 用户 (`users`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| phone | string(11) | 手机号，唯一 |
| nickname | string(50) | 昵称 |
| avatar | string(255) | 头像URL |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| last_login_at | datetime | 最后登录 |

### 行程 (`itineraries`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| creator_id | int | 创建者ID |
| destination | string(100) | 目的地 |
| days | int | 天数 |
| interests | JSON | 兴趣标签 |
| plan_results | JSON | LLM生成的多方案结果 |
| final_plan_index | int | 最终确认方案索引 |
| is_locked | bool | 是否已锁定 |
| locked_at | datetime | 锁定时间 |

### 分享链接 (`share_links`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| share_id | string(16) | 短链接ID，唯一 |
| itinerary_id | int | 关联行程 |
| creator_id | int | 创建者 |
| expire_at | datetime | 过期时间 |
| view_count | int | 访问次数 |
| is_active | bool | 是否有效 |

### 投票 (`votes`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| itinerary_id | int | 关联行程 |
| user_id | int | 投票用户 |
| plan_index | int | 方案索引 |

### 行程成员 (`itinerary_members`)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| itinerary_id | int | 关联行程 |
| user_id | int | 用户ID |
| joined_at | datetime | 加入时间 |
