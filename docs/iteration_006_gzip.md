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

### 问题

行程数据 JSON 较大（包含多个地点、描述），未压缩时传输浪费带宽。

### 解决

启用 FastAPI 内置 `GZipMiddleware`，对响应体 > 1000 字节的请求自动 gzip 压缩。

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/main.py` | 添加 `GZipMiddleware(minimum_size=1000)` |

### 验证

1. `uv run pytest` — 全部通过 ✅
2. 请求时携带 `Accept-Encoding: gzip` 即可获得压缩响应

---
## 迭代 007（规划中）：API 版本管理

- URL 路径版本 `/api/v1/` → `/api/v2/`
- 保持 v1 兼容，v2 使用新 schema

