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

### 问题

- LLM 调用 timeout 写死 300s，无法通过配置调整
- HTTP 客户端（httpx）超时无统一配置
- 地理编码失败无重试，直接 warn 不重试

### 解决

**1. Settings 新增超时配置：**

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `llm_timeout` | 120s | LLM 单次调用超时 |
| `search_timeout` | 15s | 搜索/HTTP 请求超时 |
| `geocode_timeout` | 10s | 地理编码超时 |

**2. Provider 使用可配置超时：**
- `ARKLLMProvider._call_llm()` — `timeout=300` → `timeout=settings.llm_timeout`
- `AmapSearchProvider` — 所有 `httpx.AsyncClient(timeout=15)` 改为 `timeout=self.settings.search_timeout`
- `AmapSearchProvider.geocode_address()` — `timeout=10` → `timeout=self.settings.geocode_timeout`

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/core/config.py` | 新增 `llm_timeout`、`search_timeout`、`geocode_timeout` |
| `src/tripweaver/providers/llm.py` | LLM timeout 从 300s 改为可配置 |
| `src/tripweaver/providers/amap.py` | 所有 httpx 超时改为可配置 |

### 验证

1. `uv run pytest` — 全部通过 ✅
2. 可通过环境变量 `LLM_TIMEOUT`、`SEARCH_TIMEOUT`、`GEOCODE_TIMEOUT` 覆盖默认值

---
## 迭代 006（规划中）：前端体验优化

- 行程生成 loading 状态优化（增加进度提示）
- 地图交互优化（拖拽、缩放）
- 移动端适配

