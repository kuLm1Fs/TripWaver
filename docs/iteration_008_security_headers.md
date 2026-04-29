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

### 问题

缺少安全响应头，容易受到 XSS、点击劫持等攻击。

### 解决

新增 `SecurityHeadersMiddleware`，为所有响应添加：

| 响应头 | 值 | 作用 |
|--------|-----|------|
| `X-Content-Type-Options` | nosniff | 阻止 MIME 类型 sniffing |
| `X-Frame-Options` | DENY | 防止页面被 iframe 嵌入 |
| `X-XSS-Protection` | 1; mode=block | 浏览器 XSS 过滤器 |
| `Referrer-Policy` | strict-origin-when-cross-origin | 控制 referrer 发送策略 |

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/core/security_headers.py` | 新增，安全响应头中间件 |
| `src/tripweaver/main.py` | 注册 `SecurityHeadersMiddleware` |

### 验证

1. `uv run pytest` — 全部通过 ✅

---
## 迭代 009（规划中）：JWT 刷新 token

- 短期 access_token + 长期 refresh_token
- refresh_token 存 Redis，支持撤销
