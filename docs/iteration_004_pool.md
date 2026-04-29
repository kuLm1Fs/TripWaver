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

### 问题

`create_async_engine` 未配置连接池参数，高并发下容易耗尽连接。

### 解决

在 `Settings` 中添加连接池配置参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `db_pool_size` | 10 | 连接池基础大小 |
| `db_max_overflow` | 20 | 允许超出的最大连接数 |

`create_async_engine` 配置项：
- `pool_pre_ping=True` — 拿连接前先验证连通性，避免拿到已断开的连接
- `pool_recycle=3600` — 1小时回收连接，避免连接被服务端关闭

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/core/config.py` | 新增 `db_pool_size`、`db_max_overflow` 配置项 |
| `src/tripweaver/core/db.py` | `create_async_engine` 传入连接池参数 |

### 验证

1. `uv run pytest` — 全部通过 ✅
2. 可通过环境变量 `DB_POOL_SIZE`、`DB_MAX_OVERFLOW` 覆盖默认值

---
## 迭代 005（规划中）：请求超时与重试机制

- LLM 调用超时配置（当前 hardcoded 120s）
- 地理编码失败重试（当前直接 warn，不重试）
- HTTP 客户端重试策略（搜索服务）

