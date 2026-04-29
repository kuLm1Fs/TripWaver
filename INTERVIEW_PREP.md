# TripWeaver 面试准备文档

## 项目概述

TripWeaver 是一个 AI 行程规划平台，支持多方案生成、群组投票、路线规划等功能。

**技术栈：**
- 后端：FastAPI + async SQLAlchemy + PostgreSQL + JWT 认证
- 前端：Vue 3 + TypeScript + Element Plus
- LLM：Volcengine Ark（doubao-seed-2-0-lite-260215）
- 地图：高德地图 API（POI 搜索、地理编码、路径规划）
- 测试：pytest + pytest-asyncio

---

## 架构设计

### 1. 异步并发架构

**问题：** 单个 LLM 调用串行生成 3 个方案，耗时约 200s。

**解决方案：** `asyncio.gather` 并行调用 3 个 LLM agent，每个 agent 用不同 prompt 生成一种风格（休闲美食、地标打卡、小众探店）。

```python
# llm.py
results = await asyncio.gather(
    self._generate_single_plan(request, style)
    for style in PLAN_STYLES
)
```

**追问：**
- 如果其中一个失败了怎么办？→ 单个失败不影响其他，至少一个成功即可返回
- 并行调用有没有数量限制？→ 目前固定 3 个，可扩展

---

### 2. 坐标回填机制

**问题：** LLM 生成的地点没有经纬度，地图无法展示。

**解决流程：**
1. 优先从搜索候选结果中匹配（精确名称 > 模糊匹配）
2. 匹配不到的调用高德地理编码 API 回填
3. 使用 `coord_cache` 避免重复 geocoding

**关键代码模式：**
```python
# Duck typing 而非 isinstance，避免 mock 测试失败
if hasattr(self.amap_provider, "geocode_address"):
    lng, lat = await self.amap_provider.geocode_address(address)
```

**追问：**
- 为什么不直接问 LLM 返回坐标？→ LLM 幻觉问题，坐标不可信
- Pydantic model 和 dict 混合怎么处理？→ `hasattr` 判断，支持两种场景

---

### 3. 数据库关联删除

**问题：** 删除行程时需要清理所有关联数据。

```python
# 级联删除关联数据
await db.execute(delete(Vote).where(Vote.itinerary_id == itinerary_id))
await db.execute(delete(ShareLink).where(ShareLink.itinerary_id == itinerary_id))
await db.execute(delete(ItineraryMember).where(ItineraryMember.itinerary_id == itinerary_id))
await db.delete(itinerary)
```

**追问：**
- 为什么不用数据库外键级联？→ 业务逻辑需要先清理其他表的数据（如日志、投票记录）
- 如何保证原子性？→ 全部操作在同一个事务中，失败回滚

---

### 4. 前端状态管理

**投票状态流转：**
```
未投票 → 已投票 → 已锁定
```

**锁定逻辑：** 投票最多者胜出，无投票则默认方案一。

---

## 关键问题与解决方案

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| 15 | 地图 POI 不显示 | LLM 生成地点无坐标 | 坐标回填流程 |
| 16 | plan_options dict 坐标未回填 | 去重导致同名地点被跳过 | 移除去重，遍历所有实例 |
| 17 | LLM 生成太慢（200s） | 串行调用 3 次 | 并行 asyncio.gather |

---

## 可能在面试中被问到的问题

### Q1: asyncio.gather 和 asyncio.create_task 的区别？

- `create_task` 创建任务但不等待，适合需要手动管理生命周期的场景
- `gather` 批量执行并返回所有结果，任一失败默认整体失败，可用 `return_exceptions=True` 捕获

### Q2: FastAPI 中 Depends 的作用？

依赖注入系统，用于：
- 获取当前用户 `get_current_user_id`
- 获取数据库会话 `get_db`
- 业务逻辑复用（认证、权限校验）

### Q3: SQLAlchemy async 的优势？

- 非阻塞 IO，在等待数据库响应时可以切换到其他协程
- 配合 `uvicorn --workers` 或 `gunicorn` 实现并发

### Q4: 如何保证接口安全性？

- JWT Token 认证（PyJWT）
- 401 自动跳转登录页
- 权限校验（只有创建者可删除/锁定行程）
- SQL 注入防护（ORM 参数化查询）

### Q5: 地图路线规划的实现？

1. 从行程方案提取有坐标的 POI 列表
2. 调用高德步行路径规划 API `https://restapi.amap.com/v3/direction/walking`
3. 切割成多段，返回总距离和总耗时

### Q6: 前端 TypeScript 类型定义的好处？

- 编译期检查，消灭运行时类型错误
- IDE 自动补全，提升开发效率
- 接口变更时提供明确的影响范围

### Q7: 如果 LLM 返回的 JSON 格式错误怎么办？

- `json.loads` 捕获 `JSONDecodeError` 重试
- 最多重试 3 次
- 格式化 prompt 要求严格 JSON 输出

---

## 代码规范

- Python 3.12+，全类型注解
- line-length 100
- 中文注释和 docstring
- 测试覆盖正常路径和边界情况
- 数据库测试用 mock，不连真实 DB
