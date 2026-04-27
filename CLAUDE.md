# TripWeaver 开发工作流

## 固定开发流程

每个模块必须严格按以下步骤执行：

1. **写代码** — 实现模块功能
2. **写测试** — 覆盖正常路径和边界情况
3. **跑测试** — `uv run pytest` 全部通过才能继续
4. **提交 git** — 测试通过后立即 commit，message 用中文，格式：`feat: xxx` 或 `fix: xxx`

禁止跳过任何步骤。测试不通过不能提交。

## 测试规范

- 测试文件放在 `tests/` 目录，命名 `test_<模块名>.py`
- 异步测试用 `@pytest.mark.asyncio`
- 数据库相关测试用 mock（FakeSession / FakeAsyncSession），不连真实 DB
- 认证相关测试用 `app.dependency_overrides` 注入 mock user
- 每个测试类/函数要有中文 docstring 说明测试场景

## 代码规范

- Python 3.12+，类型注解
- line-length 100
- 中文注释和 docstring
- 不加多余抽象，保持简洁

## 技术栈

- FastAPI + async SQLAlchemy + PostgreSQL
- JWT 认证（PyJWT）
- Pydantic 2 schema 校验
- structlog 结构化日志
- pytest + pytest-asyncio 测试
- uv 包管理

## 项目结构

```
src/tripweaver/
├── api/routes/     # HTTP 路由
├── core/           # 配置、DB、认证
├── domain/schemas/ # Pydantic schemas
├── models/         # SQLAlchemy ORM
├── providers/      # LLM/Search 抽象
└── services/       # 业务编排
```

## 数据流

```
用户请求 -> API -> PlannerService -> SearchProvider -> list[CandidatePlace] -> LLMProvider -> ItineraryResponse -> API响应
```
