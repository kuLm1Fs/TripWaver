# 迭代记录

---

## 迭代 001：可观测性增强 + 接口限流 ✅

### 完成内容

- **健康检查增强**：`/health/live`（存活）、`/health/ready`（Redis+DB 连通性，异常返 503）
- **限流**：Sliding window，每用户每 10 分钟最多 5 次 plan 调用，Redis 不可用时 fail-open
- **文档**：`docs/iteration_001_observability.md`

---

## 迭代 002：参数校验 + 友好错误提示

### 问题

1. `days=999` 这种无效参数直接打到 LLM，浪费 API 配额
2. 错误提示不够友好，用户不知道哪里填错了
3. `interests` 列表没有长度限制，可能传超大数组

### 解决

#### 1. 增强 ItineraryRequest 校验

```python
class ItineraryRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100)
    days: int = Field(default=1, ge=1, le=30)  # 已有，但需确认生效
    interests: list[str] = Field(default_factory=list, max_length=10)
    range_mode: str = Field(default="walking")
    range_minutes: int = Field(default=20, ge=5, le=120)  # 扩大上限
```

#### 2. 友好的错误响应

当前 `detail` 里是一串 location path，用户看不懂。改为：

```json
{
  "error": "参数校验失败",
  "detail": {
    "destination": "目的地不能为空",
    "days": "天数必须在 1-30 天之间"
  }
}
```

#### 3. 统一错误响应格式

所有 API 错误统一为 `{ "error": "...", "detail": {...} }`，不再混用 `{ "error": "..." }` 和 `{ "detail": "..." }` 两种格式。

---

### 修改文件

| 文件 | 操作 |
|------|------|
| `src/tripweaver/domain/schemas/base.py` | 增强 ItineraryRequest 校验 |
| `src/tripweaver/core/errors.py` | 统一错误格式，友好提示 |
| `src/tripweaver/api/routes/itineraries.py` | plan 端点移除手动校验逻辑（如有）|

### 验证

1. `days=999` → 422 with "天数必须在 1-30 天之间"
2. `destination=""` → 422 with "目的地不能为空"
3. `interests=["x"]*20` → 422 with "兴趣标签最多10个"
4. `uv run pytest` — 全部通过
