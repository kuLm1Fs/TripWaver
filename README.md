# TripWeaver

TripWeaver 是一个可扩展的旅游路线规划 Agent 后端骨架，当前先做 MVP：

- 接收用户的目的地、天数、偏好
- 通过可替换的搜索 provider 收集候选地点
- 通过可替换的 LLM provider 生成结构化 itinerary
- 暴露 HTTP API，后续方便接前端、CLI 或工作流

## 当前学习方式

当前按“一个模块一个模块手写”的方式推进，不直接铺完整代码。

固定开发顺序：

1. `core/config.py`
2. `domain/schemas.py`
3. `providers/base.py`
4. `providers/search.py`
5. `providers/llm.py`
6. `services/planner.py`
7. `api/routes/itineraries.py`
8. `main.py`
9. `tests/`

后续如果继续带你写模块，默认先回看这份 README 里的顺序和数据流。

## 项目结构含义

- `core/`
  - 放配置相关代码
  - 例如 `.env`、provider 开关、API key
- `domain/`
  - 放数据模型
  - 定义“输入长什么样、中间结果长什么样、输出长什么样”
- `providers/`
  - 放具体能力模块
  - 比如搜索 provider、LLM provider
- `services/`
  - 放业务编排层
  - 负责把 provider 串起来
- `api/`
  - 放 HTTP 路由
  - 只负责收请求和返结果
- `tests/`
  - 放测试

## 数据流

这个项目的数据流固定为：

```text
用户请求 -> API -> PlannerService -> SearchProvider -> list[CandidatePlace] -> LLMProvider -> ItineraryResponse -> API响应
```

三种核心数据状态：

- `ItineraryRequest`
  - 用户输入
- `list[CandidatePlace]`
  - 搜索阶段产出的候选地点列表
- `ItineraryResponse`
  - 最终生成的 itinerary 结果

### 为什么搜索阶段返回 `list[CandidatePlace]`

因为搜索模块的职责不是直接生成行程，而是先给后续规划模块提供“候选地点集合”。

也就是：

- `SearchProvider`
  - 回答“去哪玩”
- `LLMProvider`
  - 回答“怎么安排”

所以 `list[CandidatePlace]` 是搜索阶段的标准输出，也是搜索模块和 itinerary 生成模块之间的桥梁。

当前刻意暂缓：

- 多日复杂排期优化
- 预算、酒店、天气、地图导航
- 真实 Brave Search / OpenAI 调用链的细化容错

这些现在不做，是为了先把模块边界和最小请求流跑通；等 MVP 跑稳后再在 provider 层继续扩展。

## 技术栈

- FastAPI: 提供 API 服务
- Pydantic Settings: 管理环境变量和配置
- OpenAI SDK: 预留 LLM provider 接口
- HTTPX: 预留外部搜索 API 客户端
- Structlog: 日志
- Pytest / Ruff: 测试和静态检查
- uv: 虚拟环境、锁定依赖、运行命令

## 目录结构

```text
TripWeaver/
├── pyproject.toml
├── .python-version
├── .env.example
├── src/tripweaver/
│   ├── main.py
│   ├── api/routes/
│   ├── core/
│   ├── domain/
│   ├── providers/
│   └── services/
└── tests/
```

## 核心数据流

1. 客户端请求 `/api/v1/itineraries/plan`
2. `PlannerService` 调用搜索 provider 获取候选地点
3. `PlannerService` 调用 LLM provider 生成结构化 itinerary
4. API 返回 `ItineraryResponse`

## 环境初始化

复制环境变量模板：

```bash
cp .env.example .env
```

创建虚拟环境并同步依赖：

```bash
uv sync
```

如果你只想同步生产依赖：

```bash
uv sync --no-dev
```

如果你后面手动改了 `pyproject.toml`，重新同步：

```bash
uv sync
```

如果你想用命令直接加包，而不是手改 `pyproject.toml`：

```bash
uv add fastapi httpx openai pydantic-settings structlog "uvicorn[standard]"
uv add --dev pytest pytest-asyncio ruff
```

## 运行

开发启动：

```bash
uv run uvicorn tripweaver.main:app --reload
```

运行测试：

```bash
uv run pytest
```

代码检查：

```bash
uv run ruff check .
```

## 后续接入真实 Provider

- 搜索：在 `src/tripweaver/providers/search.py` 中补 Brave Search provider
- 模型：在 `src/tripweaver/providers/llm.py` 中补 OpenAI provider
- 编排：在 `src/tripweaver/services/planner.py` 中保留业务逻辑，不把逻辑写到路由层

## 文档入口

- FastAPI: https://fastapi.tiangolo.com/
  当前先看 path operation 和 dependency injection
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
  当前主要解决环境变量配置
- OpenAI Python SDK: https://github.com/openai/openai-python
  当前先用于 provider 抽象的落点
- Brave Search API: https://api-dashboard.search.brave.com/app/documentation
  后续在真实搜索 provider 中接入
- uv: https://docs.astral.sh/uv/
  当前先看 `uv sync`、`uv add`、`uv run`
