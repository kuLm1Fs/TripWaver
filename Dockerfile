FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

# 先复制依赖定义，利用缓存
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

# 复制源码
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .

# 构建项目本身
RUN uv sync --no-dev

EXPOSE 8000

# 启动时自动迁移 + 启动服务
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn tripweaver.main:app --host 0.0.0.0 --port 8000"]
