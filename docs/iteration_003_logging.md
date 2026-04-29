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

### 问题

当前关键操作缺少耗时和计数日志，无法：
- 量化 LLM 调用耗时
- 监控缓存命中率
- 追踪搜索阶段耗时
- 统计限流触发次数

### 解决

在关键路径打结构化指标日志：

```python
# LLM 调用
logger.info("llm_generated", plans=3, duration_ms=180000, cached=False)

# 缓存命中
logger.info("llm_cache_hit", key=cache_key, duration_ms=2)

# POI 搜索
logger.info("poi_searched", destination="南京", candidates=50, duration_ms=120)

# 限流触发
logger.warning("rate_limit_triggered", user_id=123, count=5)

# 请求完成（统一埋点）
logger.info("request_completed",
    path="/api/v1/itineraries/plan",
    method="POST",
    status=200,
    duration_ms=185000,
    cache_hit=False,
)
```

### 修改点

| 文件 | 改动 |
|------|------|
| `src/tripweaver/services/planner.py` | 搜索、LLM、缓存各阶段打耗时 |
| `src/tripweaver/core/logging.py` | 请求完成统一埋点（响应时间、状态码）|
| `src/tripweaver/core/ratelimit.py` | 限流触发打 warning 日志 |

### 验证

1. `uv run pytest` — 全部通过
2. 发起一个 plan 请求，看日志是否包含 `duration_ms`、`cache_hit` 等字段
3. 触发限流后查看是否有 `rate_limit_triggered` warning ✅

---

## 迭代 004（规划中）：数据库连接池配置

- SQLAlchemy async pool_size、max_overflow 配置
- 避免高并发时连接耗尽
