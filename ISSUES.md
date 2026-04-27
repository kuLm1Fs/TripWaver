# TripWeaver 已遇问题汇总

记录开发过程中遇到的所有问题、根因和修复状态。

---

## 1. ARK LLM 调用阻塞事件循环（已修复）

**现象**：前端发起行程生成请求后，后端日志停在"开始LLM生成行程"，之后无任何输出，前端 60 秒超时后显示"行程生成失败"。

**根因**：`ARKLLMProvider.generate_itinerary()` 中使用 `self.client.responses.create()` 是**同步阻塞调用**，直接放在 `async` 函数中会阻塞 uvicorn 的事件循环，导致整个服务器无法处理任何请求。

**修复**：
- 将 `responses.create()` 改为 `chat.completions.create()`（标准 Chat Completions API，兼容性更好）
- 用 `asyncio.to_thread()` 包装同步调用，放到线程池执行，不阻塞事件循环

**文件**：`src/tripweaver/providers/llm.py`

---

## 2. SEARCH_PROVIDER 配置错误（已修复）

**现象**：POI 搜索只返回 3 条模拟数据，不是真实高德地图数据。

**根因**：`.env` 中 `SEARCH_PROVIDER=tavily`，而工厂代码中 `tavily` 和 `brave` 会触发废弃警告并回退到 `MockSearchProvider`，不会调用高德 API。

```python
# factory.py
if settings.search_provider == "tavily" or settings.search_provider == "brave":
    warnings.warn("...deprecated for POI search...")
    return MockSearchProvider()  # ← 回退到 mock
```

**修复**：将 `.env` 中 `SEARCH_PROVIDER` 改为 `amap`。

**文件**：`.env`

---

## 3. plan_options 字段名前后端不一致（已修复）

**现象**：投票面板中方案名称和描述显示为空。

**根因**：LLM Prompt 要求生成的 JSON 字段名是 `plan_name` 和 `plan_desc`，但前端 `PlanOption` 类型定义的是 `title` 和 `description`。

后端 `ItineraryResponse.plan_options` 类型是 `list[dict]`，直接透传 LLM 原始 JSON，不做字段映射。

**修复**：统一使用 `title` / `description`。修改 LLM Prompt 和 MockLLMProvider 的输出格式，与前端 `PlanOption` 接口对齐。

**涉及文件**：
- `src/tripweaver/providers/llm_prompt.py` — JSON 模板字段名改为 `title`/`description`
- `src/tripweaver/providers/llm.py` — MockLLMProvider 同步修改
- `tests/test_llm_prompt.py`、`tests/test_providers.py` — 测试断言同步更新

---

## 4. 前端 axios 超时太短（潜在问题）

**现象**：LLM 生成通常需要 10-30 秒，复杂请求可能更久。

**现状**：`frontend/src/api/itinerary.ts` 中 axios timeout 设置为 `60000`（60 秒），LLM 生成加上高德搜索和 Tavily 攻略搜索，总耗时可能接近或超过这个值。

**建议**：将 `/itineraries/plan` 的超时单独设置为 120 秒或更长，其他接口保持 60 秒。

**文件**：`frontend/src/api/itinerary.ts`

---

## 5. ItineraryResponse 缺少 days 字段（已修复）

**现象**：TypeScript 编译报错 `Property 'days' does not exist on type 'ItineraryResponse'`。

**根因**：后端 `get_itinerary` 返回了 `days` 字段，但前端 `ItineraryResponse` 接口没有定义。

**修复**：在 `ItineraryResponse` 中添加 `days?: number`。

**文件**：`frontend/src/types/itinerary.ts`

---

## 6. RouteSegment.from/to 类型不匹配（已修复）

**现象**：TypeScript 编译报错，后端返回数字但前端定义为字符串。

**根因**：后端 `plan_walking_route` 返回的 `from`/`to` 是 `int` 索引，前端 `RouteSegment` 接口定义为 `string`。

**修复**：将前端 `RouteSegment.from` 和 `to` 改为 `number` 类型。

**文件**：`frontend/src/types/itinerary.ts`

---

## 7. AMap.Polyline 类型声明缺失（已修复）

**现象**：TypeScript 编译报错 `Property 'Polyline' does not exist on type 'typeof AMap'`。

**根因**：`MapView.vue` 中使用了 `AMap.Polyline` 绘制路线，但 `amap.d.ts` 类型声明文件中没有定义这个类。

**修复**：在 `amap.d.ts` 中添加 `Polyline` 类声明。

**文件**：`frontend/src/types/amap.d.ts`

---

## 8. 未使用的变量导致 TypeScript 警告（已修复）

**现象**：多个文件出现 `'xxx' is declared but its value is never read` 警告。

**涉及项**：
- `App.vue` 中 `useRoute` 导入未使用 → 已移除
- `MapView.vue` 中 `searchInputRef` 未使用 → 已移除
- `TripDetailPage.vue` 中 `authStore` 导入未使用 → 已移除

---

## 9. 高德 API biz_ext 返回类型不一致（已修复）

**现象**：POI 搜索时报错 `AttributeError: 'list' object has no attribute 'get'`，发生在 `amap.py` 第 226 行 `biz_ext.get("cost", "")`。

**根因**：高德地图 API 返回的 `biz_ext` 字段类型不固定，大部分 POI 返回 `dict`，但部分 POI（如某些景点）返回 `list`（空数组 `[]`）。代码假设它一定是 `dict`，直接调用 `.get()` 导致崩溃。

**修复**：在调用 `.get()` 前增加类型检查，非 dict 时回退为空字典。

```python
biz_ext = poi.get("biz_ext", {})
if not isinstance(biz_ext, dict):
    biz_ext = {}
```

**文件**：`src/tripweaver/providers/amap.py`

---

## 10. 范围选择器 UI 间距问题（已修复）

**现象**：用户反馈游玩范围选择器与上方时间轴太紧凑，估算距离文字位置偏高。

**修复**：
- 增加 `.range-slider-wrap` 的 `margin-top` 和 `padding`
- 增加 `.range-hint` 的 `margin-top` 从 8px → 16px
- 添加背景色和圆角区分区域

**文件**：`frontend/src/components/TripForm.vue`

---

## 11. JWT 密钥长度不足安全警告（已修复）

**现象**：后端启动/接口请求时日志打印警告 `InsecureKeyLengthWarning: The HMAC key is 25 bytes long, which is below the minimum recommended length of 32 bytes for SHA256.`

**根因**：默认 `jwt_secret` 配置长度只有25字节，不符合SHA256算法要求的最小32字节安全长度，存在被暴力破解的风险。

**修复**：将默认JWT密钥修改为长度38字节的随机字符串 `tripweaver-dev-secret-1234567890abcdefghij`，符合安全要求。生产环境要求通过环境变量传入更强的随机密钥。

**文件**：`src/tripweaver/core/config.py`

---

## 12. 模块重构导入错误（已修复）

**现象**：测试运行报错 `ModuleNotFoundError: No module named 'tripweaver.domain.schemas.auth'; 'tripweaver.domain.schemas' is not a package`

**根因**：原来的单文件 `schemas.py` 重构为 `schemas` 包，拆分多个子模块后，`__init__.py` 未正确导出所有类型，原有导入路径失效。

**修复**：
1. 创建 `src/tripweaver/domain/schemas/__init__.py`，统一导出所有类型
2. 调整所有导入路径为 `from tripweaver.domain.schemas import xxx`

**涉及文件**：所有导入schemas的文件

---

## 13. 原有接口测试用例鉴权失败（待修复）

**现象**：原有 `test_plan_itinerary_success` 等测试用例执行失败，返回401 Unauthorized

**根因**：接口新增登录鉴权后，测试用例未携带有效JWT Token，请求被权限拦截。

**修复方案**：测试用例中模拟登录获取有效Token，或者Mock权限校验绕过鉴权。

**状态**：待修复

---

## 14. SQLAlchemy 隐式 ROLLBACK 日志（正常现象）

**现象**：每个请求结束后日志打印 `INFO sqlalchemy.engine.Engine ROLLBACK`

**根因**：异步Session在请求结束后没有显式commit/rollback时，SQLAlchemy会自动触发ROLLBACK回滚未提交的事务，属于正常的资源清理行为，不影响业务逻辑。

**状态**：无需修复，不影响功能

---

## 问题优先级

| 优先级 | 问题 | 状态 |
|---|---|---|
| P0 | ARK LLM 调用阻塞事件循环 | 已修复 |
| P0 | SEARCH_PROVIDER 配置错误 | 已修复 |
| P0 | 高德 biz_ext 返回类型崩溃 | 已修复 |
| P1 | plan_options 字段名不一致 | 已修复 |
| P1 | JWT 密钥长度不足安全警告 | 已修复 |
| P2 | axios 超时太短 | 待评估 |
| P2 | 模块重构导入错误 | 已修复 |
| P2 | 原有接口测试用例鉴权失败 | 待修复 |
| P3 | 其他 TS 类型/样式问题 | 已修复 |
| P4 | SQLAlchemy 隐式 ROLLBACK 日志 | 无需修复 |
