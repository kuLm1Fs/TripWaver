# 迭代记录

---

## 迭代 001：可观测性增强 + 接口限流

### 问题

1. `/health` 端点只返回 `{"status":"ok"}`，不检查 Redis/DB 实际连通性
2. `/plan` 接口无任何限流，用户可高频调用浪费 LLM 配额
3. 无请求计数、错误率等关键指标

### 解决

#### 1. 健康检查增强 (`src/tripweaver/core/health.py`)

新增 `/health/ready` 深度检查：

```
GET /health/ready
→ 200 OK: { "status": "ok", "redis": "ok", "db": "ok" }
→ 503 Service Unavailable: { "status": "degraded", "redis": "error", "db": "ok" }
```

`/health` 保留为简单检查（应用存活即可），`/health/ready` 用于 k8s/负载均衡判断是否要路由流量过来。

#### 2. 限流 (`src/tripweaver/core/ratelimit.py`)

对 `/plan` 接口加 Sliding Window 限流：

- 每人每 10 分钟最多 5 次规划请求
- 基于 IP + user_id 组合维度
- 触发限流返回 429 Too Many Requests

限流计数存储在 Redis，利用已有 Redis 连接，不增加外部依赖。

#### 3. 注册路由

`src/tripweaver/main.py` 新增：

```python
app.add_route("/health/ready", ...
app.add_route("/health/live", ...
```

---

### 修改文件

| 文件 | 操作 |
|------|------|
| `src/tripweaver/core/health.py` | 新建，健康检查逻辑 |
| `src/tripweaver/core/ratelimit.py` | 新建，滑动窗口限流 |
| `src/tripweaver/api/routes/itineraries.py` | plan 端点加 `@limiter` 装饰器 |
| `src/tripweaver/main.py` | 注册健康检查路由 |

### 验证

1. `uv run pytest` — 全部通过
2. Redis 断开时 `/health/ready` 返回 503
3. 10 分钟内第 6 次 `/plan` 请求返回 429
4. 限流后查看 Redis 中计数 key 是否正确递增
