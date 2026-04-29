# 迭代记录

---
## 迭代 001：可观测性增强 + 接口限流 ✅

- `/health/live` + `/health/ready`
- Sliding window 限流，fail-open
- 文档：`docs/iteration_001_observability.md`

---
## 迭代 002：参数校验 + 友好错误提示 ✅

- `ItineraryRequest` 增强校验（interests max 10，custom_tags max 20，range_minutes 上限 120）
- 422 错误返回字段级中文提示
- 统一错误响应格式 `{ "error": "...", "detail": {...} }`
- 文档：`docs/iteration_002_validation.md`

---
## 迭代 003：Structured Logging 增强 — 关键指标 ✅

- `PlannerService` 搜索、LLM、缓存各阶段打耗时日志
- `LoggingMiddleware` 请求完成统一埋点（响应时间、状态码）
- 限流触发打 warning 日志
- 文档：`docs/iteration_003_logging.md`

---

## 迭代 004：数据库连接池配置 ✅

- `Settings` 新增 `db_pool_size`(10) 和 `db_max_overflow`(20)
- `create_async_engine` 配置 `pool_pre_ping` 和 `pool_recycle`
- 文档：`docs/iteration_004_pool.md`

---

## 迭代 005：超时与重试机制 ✅

- Settings 新增 `llm_timeout`(120s)、`search_timeout`(15s)、`geocode_timeout`(10s)
- ARKLLMProvider 和 AmapSearchProvider 使用可配置超时
- 文档：`docs/iteration_005_timeout.md`

---

## 迭代 006：API 响应压缩（gzip） ✅

- GZipMiddleware(minimum_size=1000) 自动压缩大响应
- 文档：`docs/iteration_006_gzip.md`

---

## 迭代 007：请求 body 大小限制 ✅

- BodySizeLimitMiddleware 限制 POST/PUT/PATCH ≤ 1MB，超限返回 413
- 文档：`docs/iteration_007_body_limit.md`

---

## 迭代 008：安全响应头 ✅

- SecurityHeadersMiddleware 添加 X-Content-Type-Options、X-Frame-Options 等
- 文档：`docs/iteration_008_security_headers.md`

---

## 迭代 009：JWT 刷新 token ✅

### 问题

只有 access_token，过期后用户需重新登录。

### 解决

- `LoginResponse` 新增 `refresh_token` 字段
- `create_refresh_token()` 生成 7 天有效的 refresh_token
- 新增 `POST /auth/refresh` 接口，用 refresh_token 换新 access_token
- `verify_token()` 增加 `expected_type` 参数，区分 access/refresh token

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/core/config.py` | 新增 `refresh_token_expire_days`(7天) |
| `src/tripweaver/core/security.py` | 新增 `create_refresh_token()`，`verify_token()` 支持 type 校验 |
| `src/tripweaver/api/routes/auth.py` | 登录返回 refresh_token，新增 refresh 接口 |
| `src/tripweaver/domain/schemas/auth.py` | `LoginResponse` 新增 `refresh_token` |

### 验证

1. `uv run pytest` — 全部通过 ✅
2. 调用 `/auth/refresh` 接口验证 token 刷新

---
## 迭代 010（规划中）：接口限流细化

- 按 user_id 限流 → 按 IP + user_id 组合限流
- 不同接口不同的限流阈值（plan 接口 vs 普通查询）
