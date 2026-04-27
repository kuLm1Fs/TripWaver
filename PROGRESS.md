# TripWeaver 模块进度

## MVP 已完成

- [x] **core/config.py** — Settings 配置管理，环境变量加载，向后兼容 BRAVE_API_KEY
- [x] **core/db.py** — async SQLAlchemy 引擎、会话工厂、Base
- [x] **core/redis.py** — Redis 客户端连接
- [x] **core/security.py** — JWT token 生成和验证
- [x] **core/deps.py** — FastAPI 依赖注入（get_current_user, get_current_user_id）
- [x] **core/logging.py** — structlog 配置、LoggingMiddleware（request_id、耗时日志）
- [x] **core/errors.py** — 全局异常处理（HTTPException/ValidationError/通用异常）
- [x] **domain/schemas/** — Pydantic schemas 包（base/auth/share/vote）
- [x] **providers/base.py** — SearchProvider / LLMProvider 抽象接口
- [x] **providers/search.py** — MockSearchProvider + TavilySearchProvider
- [x] **providers/llm.py** — MockLLMProvider + ARKLLMProvider（火山方舟）
- [x] **providers/factory.py** — 根据配置构建 provider 实例
- [x] **providers/llm_prompt.py** — LLM prompt 构建（三方案格式）
- [x] **services/planner.py** — PlannerService 业务编排（搜索→LLM→行程）
- [x] **models/** — SQLAlchemy ORM（User, Itinerary, ItineraryMember, ShareLink, Vote）
- [x] **api/routes/auth.py** — 手机验证码登录、JWT 签发
- [x] **api/routes/itineraries.py** — 行程规划接口（POST /plan）
- [x] **api/routes/itinerary_ext.py** — 分享链接、投票、锁定/解锁
- [x] **main.py** — FastAPI 应用入口，路由注册，CORS + 日志 + 异常处理中间件
- [x] **Alembic 迁移** — migrations 目录 + 初始表结构迁移脚本
- [x] **Docker 容器化** — Dockerfile + docker-compose.yml（App + PG + Redis）
- [x] **.env.example** — 补全所有配置变量
- [x] **.dockerignore** — 排除 .venv/tests/__pycache__
- [x] **74 个测试全部通过**

## 后续可优化

### 代码清理

- [ ] **planner.py 移除 TODO 注释** — 实际已完成但注释仍写着"没有具体实现"
- [ ] **修复 utcnow() 废弃警告** — itinerary_ext.py 中 5 处 datetime.utcnow() 需改为 datetime.now(datetime.UTC)

### 测试补充

- [ ] **TavilySearchProvider 测试** — 当前只测了 Mock，真实 provider 无测试
- [ ] **ARKLLMProvider 测试** — 同上，需要 mock httpx/SDK 调用
- [ ] **auth 路由测试** — 登录流程（新用户创建、老用户登录、验证码错误）无测试

### 功能扩展

- [ ] **structlog 集成到业务代码** — 目前只在 logging.py 中使用，路由/服务层未接入
- [ ] **行程编辑/删除接口** — 目前只能创建和锁定，无 CRUD 完整操作
- [ ] **用户资料接口** — 修改昵称、头像等
- [ ] **多日复杂排期优化** — README 提及的后续计划
- [ ] **预算、酒店、天气、地图导航** — README 提及的后续计划
